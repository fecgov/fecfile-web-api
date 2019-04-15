import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';

/**
 * Used for displaying HTML with innerHTML.
 */

@Pipe({
  name: 'safeHTML'
})
export class SafeHTMLPipe implements PipeTransform {

  constructor(private sanitizer:DomSanitizer){}

  transform(html: any): any {
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
