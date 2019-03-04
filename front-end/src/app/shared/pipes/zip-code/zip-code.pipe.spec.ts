import { ZipCodePipe } from './zip-code.pipe';

describe('ZipCodePipe', () => {
  it('create an instance', () => {
    const pipe = new ZipCodePipe();
    expect(pipe).toBeTruthy();
  });
});
