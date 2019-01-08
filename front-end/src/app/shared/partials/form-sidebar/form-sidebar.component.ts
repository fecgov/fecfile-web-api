import { Component, Input, OnInit } from '@angular/core';
import {NgbTooltipConfig} from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'form-sidebar',
  templateUrl: './form-sidebar.component.html',
  styleUrls: ['./form-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class FormSidebarComponent implements OnInit {

  @Input() sidebarLinks: any = [];
  @Input() title: string = '';

  public itemSelected: string = '';
  public additionalItemSelected: string = '';
  public additionalOptions: Array<any> = [];

  private _indexOfItemSelected: number = null;

  constructor(
    private _config: NgbTooltipConfig
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    console.log('this.sidebarLinks: ', this.sidebarLinks);
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');

    this.sidebarLinks.findIndex((el, index) => {
      if (el.type.value === this.itemSelected) {
        this._indexOfItemSelected = index;
      }
    });
  }

  public selectedAdditionalOption(additionalItem): void {
    console.log('selectedAdditionalOption: ');

    let additionalItemIndex: number = null;

    this.additionalItemSelected = additionalItem.getAttribute('value');
    this.sidebarLinks[this._indexOfItemSelected].type.options.findIndex((el, index) => {
      if (this.additionalItemSelected === el.value) {
        additionalItemIndex = index;
      }
    });

    this.additionalOptions = this.sidebarLinks[this._indexOfItemSelected].type.options[additionalItemIndex].options;

    console.log('this.additionalOptions: ', this.additionalOptions);
  }
}
