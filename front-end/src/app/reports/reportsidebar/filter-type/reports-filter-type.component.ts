import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList } from '@angular/core';

/**
 * A component for the Category Type filter options.
 */
@Component({
    selector: 'app-reports-filter-type',
    templateUrl: './reports-filter-type.component.html',
    styleUrls: ['./reports-filter-type.component.scss'],
})
  export class ReportsFilterTypeComponent implements OnInit{

    @Input()
    public categoryType: any;

    public constructor(public elRef: ElementRef) { }

    /**
     * Init the component.
     */
    public ngOnInit(): void {
      this.clearHighlight();
    }


    /**
     * When an option is clicked, remove any highlighting applied by
     * the search scroll feature.
     */
    public clickTypeOption() {
      this.clearHighlight();
    }


    /**
     * Remove the highlighting.
     */
    private clearHighlight() {
      this.categoryType.highlight = '';
    }
}
