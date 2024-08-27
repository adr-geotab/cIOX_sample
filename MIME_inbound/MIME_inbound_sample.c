#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <net/if.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "functions.h"

// Function to handle CAN messages
void handle_can_message(int sockfd, struct can_frame *frame, int *messaging_index, int *inbound_tx_index, int *type_captured_length, int *mime_type_length, int *mime_type_max_frame, char **mime_type_buffer, int *content_length_captured_length, uint8_t *mime_content_size_little_endian, int *mime_content_size, int *mime_content_max_frame, int *mime_content_captured_length, uint8_t **mime_content_buffer) {
    static struct can_frame last_frame;
    static int first_message = 1;

    if (!first_message) {
        classify_can_frame(frame, &last_frame);
    } else {
        first_message = 0;
        classify_can_frame(frame, frame);
    }

    last_frame = *frame;

    if ((frame->can_id & CAN_EFF_MASK) == 0x00010000) {
        if (*messaging_index == 0) {
            uint8_t payload[] = {0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A};
            send_can_frame(sockfd, 0x0002ABCD, payload, sizeof(payload));
            printf("Poll Response (Handshake)\n");
        } else {
            uint8_t payload[] = {0x00};
            send_can_frame(sockfd, 0x0002ABCD, payload, sizeof(payload));
            printf("Poll Response\n");
        }
        (*messaging_index)++;
    } else if ((frame->can_id & CAN_EFF_MASK) == 0x0014ABCD) {
        if (*messaging_index == 3) {
            uint8_t payload[] = {0x01, 0x01, 0x70, 0x10, 0x01, 0x00};
            send_can_frame(sockfd, 0x001DABCD, payload, sizeof(payload));
            printf("Send External Device ID\n");
        }
        (*messaging_index)++;
    } else if ((frame->can_id & CAN_EFF_MASK) == 0x000BABCD) {
        if (*inbound_tx_index == 0) {
            *mime_type_length = frame->data[1];
            *mime_type_max_frame = (*mime_type_length + 2) / 8;

            *mime_type_buffer = (char *)malloc(*mime_type_length + 1);
            if (*mime_type_buffer == NULL) {
                perror("malloc");
                exit(1);
            }
            memset(*mime_type_buffer, 0, *mime_type_length + 1);

            *mime_content_buffer = (uint8_t *)malloc(*mime_content_size);
            if (*mime_content_buffer == NULL) {
                perror("malloc");
                exit(1);
            }
            memset(*mime_content_buffer, 0, *mime_content_size);
        }

        for (int i = 0; i < frame->can_dlc; i++) {
            if ((*type_captured_length < *mime_type_length) && (*inbound_tx_index != 0 || i >= 2)) {
                (*mime_type_buffer)[*type_captured_length] = frame->data[i];
                (*type_captured_length)++;
            } else if ((*content_length_captured_length < 4) && (*inbound_tx_index != 0 || i >= 2)) {
                mime_content_size_little_endian[*content_length_captured_length] = frame->data[i];
                (*content_length_captured_length)++;
                if (*content_length_captured_length == 3) {
                    *mime_content_size = mime_content_size_little_endian[0] | (mime_content_size_little_endian[1] << 8) | (mime_content_size_little_endian[2] << 16) | (mime_content_size_little_endian[3] << 24);
                    *mime_content_max_frame = (6 + *mime_type_length + *mime_content_size) / 8;

                    // Reallocate buffer for MIME content based on the new size
                    *mime_content_buffer = (uint8_t *)realloc(*mime_content_buffer, *mime_content_size);
                    if (*mime_content_buffer == NULL) {
                        perror("realloc");
                        exit(1);
                    }
                }
            } else if ((*mime_content_captured_length < *mime_content_size) && (*inbound_tx_index != 0 || i >= 2)) {
                (*mime_content_buffer)[*mime_content_captured_length] = frame->data[i];
                (*mime_content_captured_length)++;
            }
        }

        (*inbound_tx_index)++;
    }
}

int main() {
    int sockfd;
    struct sockaddr_can addr;
    int nbytes;
    struct can_frame frame;
    int messaging_index = 0;
    int inbound_tx_index = 0;
    int type_captured_length = 0;
    int mime_type_length = 0;
    int mime_type_max_frame = 0;
    int content_length_captured_length = 0;
    char *mime_type_buffer = NULL;
    uint8_t mime_content_size_little_endian[4] = {0};
    int mime_content_size = 1;
    int mime_content_max_frame = 0;
    int mime_content_captured_length = 0;
    uint8_t *mime_content_buffer = NULL;

    printf("\n== MIME Inbound Messaging Sample ==\n");
    printf("This script receives, re-constructs, and decodes MIME messages from the MyG server.\n");

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
            handle_can_message(sockfd, &frame, &messaging_index, &inbound_tx_index, &type_captured_length, &mime_type_length, &mime_type_max_frame, &mime_type_buffer, &content_length_captured_length, mime_content_size_little_endian, &mime_content_size, &mime_content_max_frame, &mime_content_captured_length, &mime_content_buffer);
        }

        if (mime_content_captured_length == mime_content_size) {
            printf("\n\033[92mSUCCESS! The MIME message has been received.\033[0m\n");
            printf("MIME Type: %s\n", mime_type_buffer);
            printf("MIME Payload: ");
            for (int i = 0; i < mime_content_captured_length; i++) {
                printf("%c", mime_content_buffer[i]);
            }
            printf("\n");

            free(mime_type_buffer);
            free(mime_content_buffer);
            mime_type_buffer = NULL;
            mime_content_buffer = NULL;

            break;
        }
    }

    close(sockfd);
    return 0;
}