#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "functions.h"

// Function to construct the payload given the message string
void construct_payload(const char *message_to_send, uint8_t ***nested_payload, int *num_payloads, int *total_payload_size) {
    int message_length = strlen(message_to_send);

    *total_payload_size = 3 + message_length;
    uint8_t *total_payload = (uint8_t *)malloc(*total_payload_size);
    total_payload[0] = 0x00;
    total_payload[1] = (uint8_t)(message_length & 0xFF);
    total_payload[2] = (uint8_t)((message_length >> 8) & 0xFF);
    memcpy(&total_payload[3], message_to_send, message_length);

    *num_payloads = (*total_payload_size + 6) / 7;
    *nested_payload = (uint8_t **)malloc(*num_payloads * sizeof(uint8_t *));
    
    for (int i = 0; i < *num_payloads; i++) {
        int payload_size = (i == *num_payloads - 1) ? (*total_payload_size - i * 7 + 1) : 8;
        (*nested_payload)[i] = (uint8_t *)malloc(payload_size);
        (*nested_payload)[i][0] = (uint8_t)i;
        memcpy(&(*nested_payload)[i][1], &total_payload[i * 7], payload_size - 1);
    }
    
    free(total_payload);
}

// Function to handle CAN logic
void handle_can_message(int sockfd, struct can_frame *frame, int *messaging_index, int *datalog_index, uint8_t **nested_payload, int num_payloads, int total_payload_size) {
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
        if (*messaging_index == 2) {
            uint8_t payload[] = {0x01, 0x01, 0x70, 0x10, 0x01, 0x00};
            send_can_frame(sockfd, 0x001DABCD, payload, sizeof(payload));
            printf("Send External Device ID\n");
            (*messaging_index)++;
        } else if (*datalog_index - 1 <= num_payloads && *datalog_index != 0) {
            int payload_size = (total_payload_size - (*datalog_index - 2) * 7 + 1);
            send_can_frame(sockfd, 0x001EABCD, nested_payload[*datalog_index - 2], payload_size);
            printf("Send Multi-Frame Log %d\n", *datalog_index - 1);
        } else if (*datalog_index == num_payloads + 2) {
            printf("\033[92mSUCCESS! The 0x1E message has been transmitted to the GO and will be pushed to the MyG cloud.\033[0m\n");
        }
        (*datalog_index)++;
    }
}

int main() {
    int sockfd;
    struct sockaddr_can addr;
    int nbytes;
    struct can_frame frame;
    int messaging_index = 0;
    int datalog_index = 0;

    char message_to_send[] = "0x1E multi-frame datalog";
    uint8_t **nested_payload;
    int num_payloads;
    int total_payload_size;

    printf("\n== Custom Messaging Script ==\n");
    printf("This script intakes and configures a user-inputted message to be transmitted to the MyGeotab cloud via 0x1E multi-frame data logs.\n");
    printf("Message to Send: %s\n\nPayload to Send:\n", message_to_send);

    construct_payload(message_to_send, &nested_payload, &num_payloads, &total_payload_size);

    for (int i = 0; i < num_payloads; i++) {
        int payload_size = (i == num_payloads - 1) ? (total_payload_size - i * 7 + 1) : 8;
        for (int j = 0; j < payload_size; j++) {
            printf("0x%02X ", nested_payload[i][j]);
        }
        printf("\n");
    }
    printf("\n");

    if (strlen(message_to_send) > 27) {
        printf("\033[93mWARNING: 0x1E multi-frame data logs support up to 27 bytes. Your message is %lu bytes.\nThe message will still send but the GO will truncate the message after byte 27.\nTo send longer messages, refer to the MIME protocol.\033[0m\n\n", strlen(message_to_send));
    }

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

    // Main logging loop
    while (1) {
        nbytes = read(sockfd, &frame, sizeof(frame));
        if (nbytes < 0) {
            perror("read");
            return 1;
        }

        if (nbytes == sizeof(frame)) {
            print_can_frame(&frame);
            handle_can_message(sockfd, &frame, &messaging_index, &datalog_index, nested_payload, num_payloads, total_payload_size);
        }
    }

    // Free memory
    for (int i = 0; i < num_payloads; i++) {
        free(nested_payload[i]);
    }
    free(nested_payload);

    close(sockfd);
    return 0;
}