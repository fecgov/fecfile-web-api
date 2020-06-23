import { ReportTypeService } from './../../../forms/form-3x/report-type/report-type.service';
import { F1mService } from './../../f1m/f1m-services/f1m.service';
import { ChangeDetectionStrategy, Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-f1m-preview',
  templateUrl: './f1m-preview.component.html',
  styleUrls: ['./f1m-preview.component.scss'],
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mPreviewComponent implements OnInit {

  @Input() reportId: string;
  @Input() affiliationData :any;
  @Input() qualificationData :any;
  @Input() treasurerData: any;
  @Input() type: string;
  @Input() step: string;

  public tooltipPlaceholder = 'Placeholder text';
  
  public reportInfo: any;

  constructor(
    private _f1mService: F1mService,
    private _reportTypeService : ReportTypeService
  ) { }

  ngOnInit() {
  }

  public printPreview(){
    this._reportTypeService.printPreviewPdf('1M','PrintPreviewPDF',undefined,this.reportId) .subscribe(res => {
        if(res) {
          if (res.hasOwnProperty('results')) {
            if (res['results.pdf_url'] !== null) {
              window.open(res.results.pdf_url, '_blank');
            }
          }
        }
    },
    (error) => {
      console.error('error: ', error);
    });
  }

}

