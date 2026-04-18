#include "circbuf.h"

/**
 * circbuf_push():
 *      Push 1 byte into circular buffer and step +1 MOD maxlen.
 *      Buffer is full if head+1 = tail
 */
uint8_t circbuf_push(Circbuf *circ, uint8_t byte_in)
{
    uint8_t next;
    next = circ->head + 1;
    if(next >= circ->maxlen)
        next = 0;
    
    // Circular buffer is full.
    if(next == circ->tail)
        return 0;

    circ->buffer[circ->head] = byte_in;
    circ->head = next;
    return 1;
}

/**
 * circbuf_pop():
 *      Takes 1 byte from circular buffer and tail +1 MOD maxlen
 *      Buffer is empty if head = tail
 */
uint8_t circbuf_pop(Circbuf *circ, uint8_t *byte_out)
{
    uint8_t next;
    if(circ->head == circ->tail)
        return 0;

    next = circ->tail + 1;
    if(next >= circ->maxlen)
        next = 0;

    *byte_out = circ->buffer[circ->tail];
    circ->tail = next;
    return 1;
}

/**
 * construct_circbuf():
 *      Initializes statically declared circbuf.
 */
void circbuf_construct(Circbuf *circbuf, uint8_t *const buffer, const uint8_t maxlen)
{
    circbuf->buffer = buffer;
    circbuf->head = 0;
    circbuf->tail = 0;
    circbuf->maxlen = maxlen;
}