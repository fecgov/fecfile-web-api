import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';

@Component({
  selector: 'report-type-sidebar',
  templateUrl: './Report-type-sidebar.component.html',
  styleUrls: ['./Report-type-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class ReportTypeSidebarComponent implements OnInit {

  //@Input() sidebarLinks: any = [];
  //@Input() searchField: any = {};
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() title: string = '';
  //@Input() cashOnHand: any = {};


  public itemSelected: string = '';
  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];

  private _indexOfItemSelected: number = null;

  public loadingData: boolean = true;
  public steps: any = {};
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};
  public currentStep: string = 'step_2';
  public step: string = '';

  constructor(
    private _config: NgbTooltipConfig,
    private _formService: FormsService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    /*this._formService
    .getTransactionCategories()
    .subscribe(res => {
      console.log('resp: ', res);

      this.sidebarLinks = res.data.transactionCategories;

      this.searchField = res.data.transactionSearchField;

      this.step = this.currentStep;

      this.loadingData = false;
    });

    console.log('this.sidebarLinks: ', this.sidebarLinks);*/
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');

    this.additionalOptions = [];

    this.sidebarLinks.findIndex((el, index) => {
      if (el.value === this.itemSelected) {
        this._indexOfItemSelected = index;
      }
    });

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }

  public selectedAdditionalOption(additionalItem): void {
    let additionalItemIndex: number = null;

    this.additionalItemSelected = additionalItem.getAttribute('value');
    this.sidebarLinks[this._indexOfItemSelected].options.findIndex((el, index) => {
      if (this.additionalItemSelected === el.value) {
        additionalItemIndex = index;
      }
    });

    this.additionalOptions = this.sidebarLinks[this._indexOfItemSelected].options[additionalItemIndex].options;

    this.status.emit({
      additionalOptions: this.additionalOptions
    });
  }
}
