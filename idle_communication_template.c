#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
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

// Boolean check if the CAN interface is up
int is_can_interface_up() {
    char cmd[256];
    char buffer[128];
    FILE *fp;

    snprintf(cmd, sizeof(cmd), "ip link show %s", CAN_INTERFACE);
    fp = popen(cmd, "r");
    if (fp == NULL) {
        perror("popen");
        return 0;
    }

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strstr(buffer, "state UP") != NULL) {
            pclose(fp);
            return 1;
        }
    }

    pclose(fp);
    return 0;
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

// Function to get CAN interface index
int get_can_interface_index(int sockfd) {
    struct ifreq ifr;
    strncpy(ifr.ifr_name, CAN_INTERFACE, sizeof(ifr.ifr_name));
    ifr.ifr_name[sizeof(ifr.ifr_name) - 1] = '\0';
    if (ioctl(sockfd, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl");
        exit(1);
    }
    return ifr.ifr_ifindex;
}

// Function to send a CAN frame
void send_can_frame(int sockfd, uint32_t can_id, uint8_t *data, size_t data_len) {
    struct can_frame frame;
    struct sockaddr_can addr;
    memset(&frame, 0, sizeof(frame));

    frame.can_id = can_id | CAN_EFF_FLAG;
    frame.can_dlc = data_len > 8 ? 8 : (uint8_t)data_len;
    memcpy(frame.data, data, frame.can_dlc);

    // Setup the address for sending
    addr.can_family = AF_CAN;
    addr.can_ifindex = get_can_interface_index(sockfd);

    // Send the CAN frame
    if (sendto(sockfd, &frame, sizeof(frame), 0, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("sendto");
        exit(1);
    }

    // Log the CAN frame
    char datetime[64];
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *t = localtime(&tv.tv_sec);
    strftime(datetime, sizeof(datetime), "%Y-%m-%d %H:%M:%S", t);
    
    printf("cIOX->GO9 | %s.%06ld | 0x%08X | 0x%01X | ", datetime, tv.tv_usec, can_id, frame.can_dlc);
    for (int i = 0; i < frame.can_dlc; i++) {
        printf("%02X", frame.data[i]);
    }
    int padding = 16 - (frame.can_dlc * 2);
    if (padding > 0) {
        printf("%*s", padding, " ");
    }
    printf(" | ");
}

// Function to print the CAN frame
void print_can_frame(struct can_frame *frame) {
    char datetime[64];
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *t = localtime(&tv.tv_sec);
    strftime(datetime, sizeof(datetime), "%Y-%m-%d %H:%M:%S", t);
    
    int padding = 17 - (frame->can_dlc * 2);
    printf("GO9->cIOX | %s.%06ld | 0x%08X | 0x%01X | ", datetime, tv.tv_usec, frame->can_id & CAN_EFF_MASK, frame->can_dlc);
    for (int i = 0; i < frame->can_dlc; i++) {
        printf("%02X", frame->data[i]);
    }
    if (padding > 0) {
        printf("%*s", padding, " ");
    }
    printf("| \n");
}

// Function to handle CAN messages
void handle_can_message(int sockfd, struct can_frame *frame, int *messaging_index) {
    if ((frame->can_id & CAN_EFF_MASK) == 0x00010000) {
        if (*messaging_index == 0) {
            uint8_t response_data[] = {0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A};
            send_can_frame(sockfd, 0x0002ABCD, response_data, sizeof(response_data));
            printf("Poll Response (Handshake)\n");
        } else {
            uint8_t response_data[] = {0x00};
            send_can_frame(sockfd, 0x0002ABCD, response_data, sizeof(response_data));
            printf("Poll Response\n");
        }
        (*messaging_index)++;
    } else if ((frame->can_id & CAN_EFF_MASK) == 0x0014ABCD) {
        if (*messaging_index == 3) {
            uint8_t response_data[] = {0x01, 0x01, 0x70, 0x10, 0x01, 0x00};
            send_can_frame(sockfd, 0x001DABCD, response_data, sizeof(response_data));
            printf("Send External Device ID\n");
        }
        (*messaging_index)++;
    }
}

int main() {
    int sockfd;
    struct sockaddr_can addr;
    int nbytes;
    struct can_frame frame;
    int messaging_index = 0;

    printf("\n== Idle Communication Template ==\n");
    printf("This script reads inbound CAN messages, responds to poll requests, and sends external device ID\n");

    setup_can_interface();

    if ((sockfd = socket(PF_CAN, SOCK_RAW, CAN_RAW)) < 0) {
        perror("socket");
        return 1;
    }

    int ifindex = get_can_interface_index(sockfd);
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifindex;
    if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    printf("Commencing communication session logging...\n\n");
    printf("Direction |          DateTime          |    ArbID   | DLC |       Data       | Description\n");
    printf("--------- | -------------------------- | ---------- | --- | ---------------- | --------------\n");

    while (1) {
        nbytes = read(sockfd, &frame, sizeof(frame));
        if (nbytes < 0) {
            perror("read");
            return 1;
        }

        if (nbytes == sizeof(frame)) {
            print_can_frame(&frame);
            handle_can_message(sockfd, &frame, &messaging_index);
        }
    }

    close(sockfd);
    return 0;
}