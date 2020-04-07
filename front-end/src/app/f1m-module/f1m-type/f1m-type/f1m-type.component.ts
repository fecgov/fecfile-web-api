import { Component, OnInit, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-f1m-type',
  templateUrl: './f1m-type.component.html',
  styleUrls: ['./f1m-type.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mTypeComponent implements OnInit {

  @Output() changeStep: EventEmitter<any> = new EventEmitter<any>();

  constructor() { }

  ngOnInit() {
  }

  public next(type:string){
    if(type){
      this.changeStep.emit({step:'step_2', type});
    }
  }

}
