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
    if(Array.isArray(records)) {
      return records.sort(function(a, b){
          if(a[args.property] < b[args.property]){
              return -1 * args.direction;
          }
          else if( a[args.property] > b[args.property]){
              return 1 * args.direction;
          }
          else{
              return 0;
          }
      });
    }
    return;
  }

}
