import { Component, OnInit, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.scss']
})
export class ValidateComponent implements OnInit, OnDestroy {
  messageSubscription: Subscription;

  public validateResults: any = {};
  public showValidateBar: boolean = false;
  public showValidateResults: boolean = false;

  constructor(
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.messageSubscription = this._messageService
      .getMessage()
      .subscribe(res => {
        if(typeof res.validateMessage === 'object') {
          if(res.validateMessage.showValidateBar) {
            this.showValidateResults = true;
            this.validateResults = res.validateMessage.validate;
            this.showValidateBar = res.validateMessage.showValidateBar;              
          } else {
            this.showValidateResults = false;
          }
        }
      });
  }

  ngOnDestroy(): void {
    this.messageSubscription.unsubscribe();
  }

  public isArray(obj : any ): boolean {
    return Array.isArray(obj);
  }

}
