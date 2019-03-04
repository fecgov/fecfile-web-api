import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'zipCode'
})
export class ZipCodePipe implements PipeTransform {

  /**
   * Formats a zip code.
   *
   * @param      {string}  zipCode  The zip code to be formatted
   */
  transform(zipCode: string): string {
      if (!zipCode) {
        return '';
      } else if (zipCode.length > 0 && zipCode.length < 6) {
        return zipCode;
      } else if (zipCode.length === 9) {
        return zipCode.substring(0, 5) + '-' + zipCode.substring(5);
      } else {
        return zipCode;
      }
  }

}
