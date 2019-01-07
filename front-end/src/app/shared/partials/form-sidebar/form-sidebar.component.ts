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

  constructor(
    private _config: NgbTooltipConfig
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    console.log('form-sidebar: ');
  }

  public selectItem(item): void {
    this.itemSelected = item.getAttribute('value');
  }
}
