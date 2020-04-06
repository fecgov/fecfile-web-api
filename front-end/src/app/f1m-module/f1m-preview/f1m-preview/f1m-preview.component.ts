import { F1mService } from './../../f1m/f1m-services/f1m.service';
import { ChangeDetectionStrategy, Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-f1m-preview',
  templateUrl: './f1m-preview.component.html',
  styleUrls: ['./f1m-preview.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mPreviewComponent implements OnInit {

  @Input() reportId: string;
  @Input() affiliationData :any
  @Input() qualificationData :any
  @Input() type: string;
  
  public reportInfo: any;

  constructor(
    private _f1mService: F1mService
  ) { }

  ngOnInit() {
    this._f1mService.getReportInfo().subscribe(response => {
      this.reportInfo = response;
    })
  }

  public printPreview(){
    alert('not implemented yet.');
  }

}

