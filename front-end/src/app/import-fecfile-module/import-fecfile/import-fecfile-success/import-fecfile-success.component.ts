import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-import-fecfile-success',
  templateUrl: './import-fecfile-success.component.html',
  styleUrls: ['./import-fecfile-success.component.scss']
})
export class ImportFecfileSuccessComponent implements OnInit {

  @Input() successMessage: any;

  constructor() { }

  ngOnInit() {
  }

}
