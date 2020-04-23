import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-f1m-candidates-table',
  templateUrl: './f1m-candidates-table.component.html',
  styleUrls: ['./f1m-candidates-table.component.scss']
})
export class F1mCandidatesTableComponent implements OnInit {

  @Input() candidatesData :any;
  @Input() step: string;
  
  constructor(public _messageService: MessageService) { }

  ngOnInit() {
  }

  public editCandidate(candidate:any){
    this._messageService.sendMessage({
      formType : 'f1m-qualification', 
      action : 'editCandidate',
      candidate
    })
  }

  public trashCandidate(candidate:any){
    this._messageService.sendMessage({
      formType : 'f1m-qualification', 
      action : 'trashCandidate',
      candidate
    })
  }

}
