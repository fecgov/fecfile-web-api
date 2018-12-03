import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service'

@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.scss']
})
export class SubmitComponent implements OnInit {

  public form_type: string = '';

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _messageService: MessageService
  ) { }

  ngOnInit() {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._messageService
      .getMessage()
      .subscribe(res => {
        if(res.form_submitted) {
          localStorage.removeItem(`form_${this.form_type}_details`);
        }
      });
  }

}
