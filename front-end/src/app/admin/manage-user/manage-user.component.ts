import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup} from '@angular/forms';

@Component({
  selector: 'app-manage-user',
  templateUrl: './manage-user.component.html',
  styleUrls: ['./manage-user.component.scss']
})
export class ManageUserComponent implements OnInit {
  website: string = '';

  treasurerName: string = '';
  treasurerEmail: string = '';
  treasurerTel: string = '';
  treasurerFax: string = '';

  asstTreasurerName: string = '';
  asstTreasurerEmail: string = '';
  asstTreasurerTel: string = '';
  asstTreasurerFax: string = '';

  frmAddUser: FormGroup;

  constructor(private _fb: FormBuilder) {
    this.frmAddUser = _fb.group({});
  }

  ngOnInit() {
  }

}
