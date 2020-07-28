import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { Router } from '@angular/router';

@Component({
  selector: 'app-import-done-contacts',
  templateUrl: './import-done-contacts.component.html',
  styleUrls: ['./import-done-contacts.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportDoneContactsComponent implements OnInit {

  constructor(private _router: Router) { }

  ngOnInit() {
    setTimeout(() => {
      this._router.navigate([`/contacts`]);
    }, 2000);
  }

}
