#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <errno.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/socket.h>
#include <net/if.h>
#include <time.h>
#include <sys/time.h>

#define CAN_INTERFACE "can0"
#define CAN_BITRATE 500000

// Check if the CAN interface is up
int is_can_interface_up() {
    char cmd[256];
    char buffer[128];
    FILE *fp;

    snprintf(cmd, sizeof(cmd), "ip link show %s", CAN_INTERFACE);
    fp = popen(cmd, "r");
    if (fp == NULL) {
        perror("popen");
        return 0; // Consider it not up if the command fails
    }

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strstr(buffer, "state UP") != NULL) {
            pclose(fp);
            return 1; // Interface is up
        }
    }

    pclose(fp);
    return 0; // Interface is not up
}

// Bring up the CAN interface with the specified bitrate
void setup_can_interface() {
    if (!is_can_interface_up()) {
        printf("Bringing up %s...\n", CAN_INTERFACE);
        char cmd[256];
        snprintf(cmd, sizeof(cmd), "sudo /sbin/ip link set %s up type can bitrate %d", CAN_INTERFACE, CAN_BITRATE);
        system(cmd);
    } else {
        printf("CAN interface %s is already up. Continuing...\n", CAN_INTERFACE);
    }
}

int main() {
    int sockfd;
    struct sockaddr_can addr;
    struct ifreq ifr;
    struct can_frame frame;
    int nbytes;
    char datetime[64];
    struct timeval tv;

    // Print header
    printf("\n== Idle Communication Template ==\n");
    printf("This script reads inbound CAN messages, responds to poll requests, and sends external device ID\n");

    // Setup CAN interface
    setup_can_interface();

    // Create a socket
    if ((sockfd = socket(PF_CAN, SOCK_RAW, CAN_RAW)) < 0) {
        perror("socket");
        return 1;
    }

    // Specify the CAN interface
    strncpy(ifr.ifr_name, CAN_INTERFACE, sizeof(ifr.ifr_name));
    ifr.ifr_name[sizeof(ifr.ifr_name) - 1] = '\0';
    if (ioctl(sockfd, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl");
        return 1;
    }

    // Setup address for the CAN interface
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    // Log table header
    printf("Commencing communication session logging...\n\n");
    printf("Direction |          DateTime          |    ArbID   | DLC |       Data       | Description\n");
    printf("--------- | -------------------------- | ---------- | --- | ---------------- | --------------\n");

    while (1) {
        // Read CAN messages
        nbytes = read(sockfd, &frame, sizeof(struct can_frame));
        if (nbytes < 0) {
            perror("read");
            return 1;
        }

        if (nbytes == sizeof(struct can_frame)) {
            // Print the CAN message
            gettimeofday(&tv, NULL);
            struct tm *t = localtime(&tv.tv_sec);
            strftime(datetime, sizeof(datetime), "%Y-%m-%d %H:%M:%S", t);
            int padding = 16 - (frame.can_dlc * 3 + (frame.can_dlc - 1));
            printf("GO9->cIOX | %s.%06ld | 0x%08X | 0x%01X | ", datetime, tv.tv_usec, frame.can_id & CAN_EFF_MASK, frame.can_dlc);
            for (int i = 0; i < frame.can_dlc; i++) {
                printf("0x%02X ", frame.data[i]);
            }
            if (padding > 0) {
                printf("%*s", padding, " ");
            }
            printf("|\n");
        }
    }

    close(sockfd);
    return 0;
}