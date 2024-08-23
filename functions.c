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
#include "functions.h"

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
void print_can_frame(const struct can_frame *frame) {
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
    printf("| ");
}

// Function to classify CAN messages
void classify_can_frame(const struct can_frame *inbound_frame, const struct can_frame *prev_outbound_frame) {

    if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x00010000) {
        printf("Poll Request\n");
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x0014ABCD) {
        printf("Acknowledgement of 0x%08X\n", prev_outbound_frame->can_id);
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x260000) {
        printf("GO Status Information Log");
        if (inbound_frame->data[0] == 0x00 && inbound_frame->data[1] == 0x00) {
            if (inbound_frame->data[2] == 0x00) {
                printf(" (Ignition off)\n");
            } else if (inbound_frame->data[2] == 0x01) {
                printf(" (Ignition on)\n");
            }
        } else if (inbound_frame->data[0] == 0x01 && inbound_frame->data[1] == 0x00) {
            if (inbound_frame->data[2] == 0x00) {
                printf(" (Modem is not ready)\n");
            } else if (inbound_frame->data[2] == 0x01) {
                printf(" (Modem is available)\n");
            }
        } else {
            printf("\n");
        }
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x040000) {
        printf("Wakeup\n");
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x1CABCD && inbound_frame->data[0] == 0x00) {
        printf("GO Accept Message to Buffer ");
        if (inbound_frame->data[1] == 0x00) {
            printf("(Failed)\n");
        } else if (inbound_frame->data[1] == 0x01) {
            printf("(Success)\n");
        }
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x1CABCD && inbound_frame->data[0] == 0x05) {
        if (inbound_frame->data[1] == 0x00) {
            printf("External Device Channel Disabled\n");
        } else if (inbound_frame->data[1] == 0x01) {
            printf("External Device Channel Enabled\n");
        }
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x0BABCD) {
        printf("TX Data\n");
    } else if ((inbound_frame->can_id & CAN_EFF_MASK) == 0x27ABCD) {
        printf("GO Multi-Frame Data (Frame %d)\n", inbound_frame->data[0]);
    } else {
        printf("Unclassified Message\n");
    }
}