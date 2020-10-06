import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'app-review-upload',
  templateUrl: './review-upload.component.html',
  styleUrls: ['./review-upload.component.scss']
})
export class ReviewUploadComponent implements OnInit {

  @Input()
  public duplicateFile: any;

  @Output()
  public reviewEmitter: EventEmitter<any> = new EventEmitter<any>();

  constructor() { }

  ngOnInit() {
  }

  public proceed() {
    this.reviewEmitter.emit('proceed');
  }

  public cancel() {
    this.reviewEmitter.emit('cancel');
  }

}
