import { describe, expect, it } from 'vitest';
import { parseEvent } from './stream';

describe('parseEvent', () => {
  it('parses each server event', () => {
    expect(parseEvent('event: safety\ndata: {"level": "urgent"}')).toEqual({
      type: 'safety',
      level: 'urgent',
    });
    expect(parseEvent('event: token\ndata: {"text": "hi "}')).toEqual({
      type: 'token',
      text: 'hi ',
    });
    expect(parseEvent('event: crisis\ndata: {}')).toEqual({ type: 'crisis' });
    expect(parseEvent('event: done\ndata: {"filtered": true}')).toEqual({
      type: 'done',
      filtered: true,
    });
  });

  it('ignores unknown events', () => {
    expect(parseEvent('event: ping\ndata: {}')).toBeNull();
  });
});
