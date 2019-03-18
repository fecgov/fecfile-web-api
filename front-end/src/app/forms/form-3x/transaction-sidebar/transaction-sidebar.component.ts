import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { MessageService } from '../../../shared/services/MessageService/message.service';


@Component({
  selector: 'transaction-sidebar',
  templateUrl: './transaction-sidebar.component.html',
  styleUrls: ['./transaction-sidebar.component.scss'],
  providers: [NgbTooltipConfig]
})
export class TransactionSidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input() transactionCategories: any = [];


  private _formType: string = '';

  constructor(
    private _config: NgbTooltipConfig,
    private _http: HttpClient,
    private _activatedRoute: ActivatedRoute,
    private _messageService: MessageService
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
  }

  public selectItem(e): void {
    this.status.emit({
      'form': '3x',
      'transactionType': e.target.value
    });

   this._messageService
     .sendMessage({
       'form': '3x',
       'transactionType': e.target.value,
     });
  }

  public on
}
