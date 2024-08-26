# Compiler and flags
CC = gcc
CFLAGS = -Wall -I. # -I. to include the current directory for header files

# Source files and objects
SRC = functions.c
OBJ = functions.o

# Targets
all: exc_idle_communication_template exc_iox_data_request exc_iox_data_request2 exc_outbound_data_transfer exc_custom_messaging exc_mime_inbound_sample

# Rules to build the executables
exc_idle_communication_template: idle_communication_template.o $(OBJ)
	$(CC) -o $@ idle_communication_template.o $(OBJ)

exc_iox_data_request: GO_IOX_data_transfer/iox_data_request.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request.o $(OBJ)

exc_iox_data_request2: GO_IOX_data_transfer/iox_data_request2.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request2.o $(OBJ)

exc_outbound_data_transfer: GO_IOX_data_transfer/outbound_data_transfer.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/outbound_data_transfer.o $(OBJ)

exc_custom_messaging: custom_messaging/custom_messaging.o $(OBJ)
	$(CC) -o $@ custom_messaging/custom_messaging.o $(OBJ)

exc_mime_inbound_sample: MIME_inbound/MIME_inbound_sample.o $(OBJ)
	$(CC) -o $@ MIME_inbound/MIME_inbound_sample.o $(OBJ)

# Rules for compiling the object files
idle_communication_template.o: idle_communication_template.c functions.h
	$(CC) $(CFLAGS) -c idle_communication_template.c -o idle_communication_template.o

GO_IOX_data_request.o: GO_IOX_data_transfer/iox_data_request.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request.c -o GO_IOX_data_request.o

GO_IOX_data_request2.o: GO_IOX_data_transfer/iox_data_request2.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request2.c -o GO_IOX_data_request2.o

outbound_data_transfer.o: GO_IOX_data_transfer/outbound_data_transfer.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/outbound_data_transfer.c -o outbound_data_transfer.o

custom_messaging.o: custom_messaging/custom_messaging.c functions.h
	$(CC) $(CFLAGS) -c custom_messaging/custom_messaging.c -o custom_messaging.o

MIME_inbound_sample.o: MIME_inbound/MIME_inbound_sample.c functions.h
	$(CC) $(CFLAGS) -c MIME_inbound/MIME_inbound.c -o MIME_inbound_sample.o

# Clean up build files
clean:
	rm -f *.o GO_IOX_data_transfer/*.o custom_messaging/*.o MIME_inbound/*.o MIME_outbound/*.o exc_idle_communication_template exc_iox_data_request exc_iox_data_request2 exc_outbound_data_transfer exc_custom_messaging exc_mime_inbound_sample