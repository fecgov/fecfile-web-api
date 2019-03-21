import { Pipe, PipeTransform, Injectable } from '@angular/core';

export enum FilterTypeEnum {
    contains = 'contains',
    startswith = 'startsWith',
    exact = 'exact',
    empty = ''
}

/**
 * A pipe for filtering an array on matched items to a 'search string'.  Specific fields may be provided for filtering.
 * The object types supported in the array are `number` and `string`.
 * The match may be defined as any field containing or starting with the 'searching string by setting the filterType to
 * a value of the enum `FilterTypeEnum`.
 */
@Pipe({
    name: 'filterPipe'
})

@Injectable()
export class FilterPipe implements PipeTransform {

    /**
     * The transform method to filter the array.
     *
     * @param items The array of items to be filtered
     * @param fields The array of field names of the items on which to search.  Nesting is supported
     *               up to 3 nodes.  For example, if the item is an object call node1 containg node2
     *               and the field to filter on is called node3, the array will be
     *              ['node1.node2.node3', 'someOtherField']
     * @param value the search string
     * @param filterType The type of search (startsWith, contains). Optional and will default to contains.
     */
    transform(items: any[], fields: Array<string>, value: string, filterType?: FilterTypeEnum): any[] {

        if (!items) {
            return [];
        }
        if (!fields || !value) {
            return items;
        }

        if (!filterType) {
            filterType = FilterTypeEnum.contains;
        }

        switch (filterType) {
            case FilterTypeEnum.contains:
                return items.filter(singleItem => this.filterFields(singleItem, fields, value, filterType));
            case FilterTypeEnum.startswith:
                return items.filter(singleItem => this.filterFields(singleItem, fields, value, filterType));
            default:
                return items.filter(singleItem => this.filterFields(singleItem, fields, value, filterType));
        }
    }


    /**
     * Filter an item in the array using all field names from fields.
     *
     * @param singleItem an items from the array being filtered
     * @param fields The array of field names of the items on which to search.  Nesting is supported
     *               up to 3 nodes.  For example, if the item is an object call node1 containg node2
     *               and the field to filter on is called node3, the array will be
     *              ['node1.node2.node3', 'someOtherField']
     * @param value the search string
     * @param filterType The type of search (startsWith, contains). Optional and will default to contains.
     * @returns true if a match is found on the singleItem
     */
    private filterFields(singleItem: any, fields: Array<string>, value: string, filterType: FilterTypeEnum): boolean {
        for (const field of fields) {

            // support nesting up to 3 levels
            const objectPathArray: any[] = field.split('.');
            const depth: number = objectPathArray.length;
            let node1: string;
            let node2: string;
            let node3: string;

            switch (depth) {
                case 0:
                    break;
                case 1:
                    node1 = objectPathArray[0];
                    // handle null
                    const node1Path = (singleItem[node1]) ? singleItem[node1] : '';
                    if (this.isMatched(node1Path, value, filterType)) {
                        return true;
                    }
                    break;
                case 2:
                    node1 = objectPathArray[0];
                    node2 = objectPathArray[1];
                    // handle null
                    const node2Path = (singleItem[node1][node2]) ? singleItem[node1][node2] : '';
                    if (this.isMatched(node2Path, value, filterType)) {
                        return true;
                    }
                    break;
                case 3:
                    node1 = objectPathArray[0];
                    node2 = objectPathArray[1];
                    node3 = objectPathArray[2];
                    // handle null
                    const node3Path = (singleItem[node1][node2][node3]) ? singleItem[node1][node2][node3] : '';
                    if (this.isMatched(node3Path, value, filterType)) {
                        return true;
                    }
                    break;
            }
        }
        return false;
    }


    /**
     * Determine if the item in the array starts with or contains the search string.
     *
     * @param itemNode node from item in the array to compare with the value
     * @param value the search string
     * @param filterType The type of search (startsWith, contains). Optional and will default to contains.
     * @returns true if a match is found on the itemNode
     */
    private isMatched(itemNode: any, value: string, filterType: FilterTypeEnum) {

        switch (filterType) {
            case FilterTypeEnum.contains:
                if (this.isMatchedContains(itemNode, value)) {
                    return true;
                } else {
                    return false;
                }
            case FilterTypeEnum.startswith:
                if (this.isMatchedStartsWith(itemNode, value)) {
                    return true;
                } else {
                    return false;
                }
            case FilterTypeEnum.exact:
                if (this.isMatchedExact(itemNode, value)) {
                    return true;
                } else {
                    return false;
                }
            default:
                return false;
        }
    }


    /**
     * Determine if there is a match on any part of the array node.
     *
     * @param itemNode node from item in the array to compare with the value
     * @param value the search string
     * @returns true if any or all of the itemNode matches the value
     */
    private isMatchedContains(itemNode: any, value: string): boolean {
        const itemType: string = this.determineObjectType(itemNode);
        switch (itemType) {
            case 'string':
                if (itemNode.toLowerCase().includes(value.toLowerCase())) {
                    return true;
                } else {
                    return false;
                }
            case 'number':
                if (itemNode.toString().includes(value)) {
                    return true;
                } else {
                    return false;
                }
            // TODO add support for date and/or timestamp
            default:
                return false;
        }
    }


    /**
     * Determine if there the array node starts with the search string.
     *
     * @param itemNode node from item in the array to compare with the value
     * @param value the search string
     * @returns true if the itemNode starts with the value
     */
    private isMatchedStartsWith(itemNode: any, value: string): boolean {
        const itemType: string = this.determineObjectType(itemNode);
        switch (itemType) {
            case 'string':

                if (itemNode.toLowerCase().startsWith(value.toLowerCase())) {
                    return true;
                } else {
                    return false;
                }
            case 'number':
                if (itemNode.toString().startsWith(value)) {
                    return true;
                } else {
                    return false;
                }
            // TODO add support for date and/or timestamp
            default:
                return false;
        }
    }


    /**
     * Determine if there the array node is an exact match of the search string.
     *
     * @param itemNode node from item in the array to compare with the value
     * @param value the search string
     * @returns true if the itemNode is an exact match
     */
    private isMatchedExact(itemNode: any, value: string): boolean {
        const itemType: string = this.determineObjectType(itemNode);
        switch (itemType) {
            case 'string':

                if (itemNode.toLowerCase() === value.toLowerCase()) {
                    return true;
                } else {
                    return false;
                }
            case 'number':
                if (itemNode.toString() === value.toLowerCase().valueOf()) {
                    return true;
                } else {
                    return false;
                }
            // TODO add support for date and/or timestamp
            default:
                return false;
        }
    }


    /**
     * Determine the object type.
     *
     * @param itemNode the object for which the type will be determined
     * @returns string of the object type
     */
    private determineObjectType(itemNode: any): string {
        return typeof itemNode;
    }

}
