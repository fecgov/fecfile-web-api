import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList } from '@angular/core';

/**
 * A component for the Category Type filter options.
 */
@Component({
    selector: 'app-transactions-filter-type',
    templateUrl: './transactions-filter-type.component.html',
    styleUrls: ['./transactions-filter-type.component.scss'],
})
  export class TransactionsFilterTypeComponent {

    @Input()
    public categoryType: any;

    public constructor(public elRef: ElementRef) { }
}
