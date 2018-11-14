import { Component, OnInit } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.scss']
})
export class ValidateComponent implements OnInit {

  public validateResults: any = {};
  public showValidateBar: boolean = false;
  public showValidateResults: boolean = false;

  constructor(
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this._messageService
      .getMessage()
      .subscribe(res => {
        if(typeof res.validateMessage === 'object') {
          this.showValidateResults = true;
          this.validateResults = res.validateMessage.validate;
          this.showValidateBar = res.validateMessage.showValidateBar;          
        }
      });
  }

  public isArray(obj : any ): boolean {
    return Array.isArray(obj);
  }

}
