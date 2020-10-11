import { Component, OnInit, Input, OnChanges, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.scss']
})
export class ProgressBarComponent implements OnInit, OnChanges {


  @Input()
  public progress: any;

  @Input()
  public progressArray: Array<number>;

  public percent: number;

  constructor() { }

  ngOnInit() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    let percent = 0;
    if (this.progressArray) {
      if (this.progressArray.length > 0) {
        percent = this.progressArray[0];
      }
    }
    this.percent = percent;
    // console.log('percent=' + this.progressArray);
  }

}
