import { Component, OnInit } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.scss']
})
export class ValidateComponent implements OnInit {

  public validate_results: any = {};

  constructor(
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
    this._messageService
      .getMessage()
      .subscribe(res => {
        this.validate_results = res.validate;
      });
  }

  public isArray(obj : any ): boolean {
    return Array.isArray(obj);
  }

}
