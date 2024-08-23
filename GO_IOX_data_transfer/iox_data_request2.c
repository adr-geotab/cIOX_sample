#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <net/if.h>
#include <time.h>
#include <sys/time.h>
#include "../functions.h"

// Function to handle CAN messages
void handle_can_message(int sockfd, struct can_frame *frame, int *messaging_index) {
    static struct can_frame last_frame; // Store the last frame
    static int first_message = 1;       // Flag to check if it's the first message

    if (!first_message) {
        classify_can_frame(frame, &last_frame); // Classify the previous frame information
    } else {
        first_message = 0; // Clear the flag after first message
        classify_can_frame(frame, frame); // Classify the previous frame information
    }

    // Store the current frame as the last frame
    last_frame = *frame;
    
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
            uint8_t response_data[] = {0x0C, 0x00, 0x00};
            send_can_frame(sockfd, 0x0025ABCD, response_data, sizeof(response_data));
            printf("Request GO Serial Number\n");
        }
        else if (*messaging_index == 4) {
            uint8_t response_data[] = {0x0C, 0x00, 0x01};
            send_can_frame(sockfd, 0x0025ABCD, response_data, sizeof(response_data));
            printf("Request GO Firmware Version\n");
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

    printf("\n== IOX Data Request Script ==\n");
    printf("This script requests and reads multi-frame data from the GO device of message type 0x27.\n");

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