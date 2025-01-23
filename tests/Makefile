CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -lm
TARGET = bc_velo
SRC = bc_velo.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

debug: CFLAGS += -g
debug: $(TARGET)

clean:
	rm -f $(TARGET) *.o

.PHONY: all clean debug
