import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'orderBy'
})
export class OrderByPipe implements PipeTransform {
  /**
   * Sorts a table column.
   *
   * @param      {Array}  records  The records to be sorted.
   * @param      {Object}  args     The arguments for sorting.
   */
  transform(records: Array<any>, args?: any): any {
    if (Array.isArray(records)) {
      return records.sort(function(a, b) {
        //first two conditions are added to also sort "null" values

        if (!a[args.property] && a[args.property] !== 0) {
          a[args.property] = '';
        }

        if (!b[args.property] && b[args.property] !== 0) {
          b[args.property] = '';
        }

        if (a[args.property] === b[args.property]) {
          return 0;
        } else if (a[args.property] < b[args.property]) {
          return -1 * args.direction;
        } else {
          return 1 * args.direction;
        }
      });
    }
    return;
  }
}
