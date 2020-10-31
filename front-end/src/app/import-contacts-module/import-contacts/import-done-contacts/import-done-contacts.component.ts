import { Component, OnInit, ChangeDetectionStrategy, Input, Output, EventEmitter } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { Router } from '@angular/router';
import { DuplicateContactsService } from '../clean-contacts/duplicate-contacts/service/duplicate-contacts.service';

@Component({
  selector: 'app-import-done-contacts',
  templateUrl: './import-done-contacts.component.html',
  styleUrls: ['./import-done-contacts.component.scss']
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportDoneContactsComponent implements OnInit {
  @Input()
  public fileName: string;

  @Input()
  public action: string;

  @Output()
  public saveStatusEmitter: EventEmitter<any> = new EventEmitter<any>();

  public done: boolean;

  constructor(private _router: Router, private _duplicateContactsService: DuplicateContactsService) {}

  ngOnInit() {
    this.done = false;
    if (this.action === 'ignore_dupe_save') {
      this._duplicateContactsService.saveContactIgnoreDupes(this.fileName, false).subscribe((res: any) => {
        this.done = true;
        this.saveStatusEmitter.emit(true);
      });
    } else if (this.action === 'merge_dupe_save') {
      this._duplicateContactsService.mergeAll(this.fileName, false).subscribe((res: any) => {
        this.done = true;
        this.saveStatusEmitter.emit(true);
      });
    }
  }

  public viewContacts() {
    this._router.navigate(['/notifications']);
  }
}
