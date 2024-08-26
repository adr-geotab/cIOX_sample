# Compiler and flags
CC = gcc
CFLAGS = -Wall -I. # -I. to include the current directory for header files

# Source files and objects
SRC = functions.c
OBJ = functions.o

# Targets
all: exc_idle_communication_template exc_iox_data_request exc_iox_data_request2 exc_outbound_data_transfer

# Rules to build the executables
exc_idle_communication_template: idle_communication_template.o $(OBJ)
	$(CC) -o $@ idle_communication_template.o $(OBJ)

exc_iox_data_request: GO_IOX_data_transfer/iox_data_request.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request.o $(OBJ)

exc_iox_data_request2: GO_IOX_data_transfer/iox_data_request2.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request2.o $(OBJ)

exc_outbound_data_transfer: GO_IOX_data_transfer/outbound_data_transfer.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/outbound_data_transfer.o $(OBJ)

# Rules for compiling the object files
idle_communication_template.o: idle_communication_template.c functions.h
	$(CC) $(CFLAGS) -c idle_communication_template.c -o idle_communication_template.o

GO_IOX_data_request.o: GO_IOX_data_transfer/iox_data_request.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request.c -o GO_IOX_data_request.o

GO_IOX_data_request2.o: GO_IOX_data_transfer/iox_data_request2.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request2.c -o GO_IOX_data_request2.o

outbound_data_transfer.o: GO_IOX_data_transfer/outbound_data_transfer.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/outbound_data_transfer.c -o outbound_data_transfer.o

# Clean up build files
clean:
	rm -f *.o GO_IOX_data_transfer/*.o exc_idle_communication_template exc_iox_data_request exc_iox_data_request2 exc_outbound_data_transfer