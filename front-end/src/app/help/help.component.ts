import { Component, OnInit } from '@angular/core';
import {SessionService} from '../shared/services/SessionService/session.service';

@Component({
  selector: 'app-help',
  templateUrl: './help.component.html',
  styleUrls: ['./help.component.scss']
})
export class HelpComponent implements OnInit {

  constructor(private _sessionService: SessionService) { }

  ngOnInit() {
  }

}
