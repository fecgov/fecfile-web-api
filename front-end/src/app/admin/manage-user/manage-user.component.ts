import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {UserModel} from './model/user.model';
import {ManageUserService} from './service/manage-user.service';

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
  users: Array<UserModel>;
  isEdit: boolean = false;
  constructor(private _fb: FormBuilder, private _userService: ManageUserService) {
    this.frmAddUser = _fb.group({
      role_ind: ['', Validators.required],
      first_name: ['', Validators.required],
      last_name: ['', Validators.required],
      phone_number: ['', [Validators.required, Validators.minLength(10)]],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit() {
    this._userService.getUsers().subscribe(res => {
          if (res.users) {
            this.users = this.mapFromUserFields(res.users);
            this.isEdit = false;
          }
        }
    );
  }

  addUser() {
    if (this.isEdit) {
      //do a put call
    } else {
      // do a post
    }
  }

  editUser(user: UserModel) {
    this.frmAddUser.reset();
    this.isEdit = true;
    this.frmAddUser.patchValue({ 'first_name': user.firstName }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'last_name': user.lastName }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'email': user.email }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'phone_number': 'test' }, { onlySelf: true });
  }

  toggleStatus(user: UserModel) {
  }

  clearForm() {
    this.frmAddUser.reset();
    this.isEdit = false;
  }

  deleteUser(user: UserModel) {
    alert('User deleted');
  }

  getStatusClass(status: boolean): string {
    if (status) {
      return 'fas fa-toggle-on fa-2x';
    } else {
      return 'fas fa-toggle-off fa-2x';
    }
  }

  mapFromUserFields(users: any): Array<UserModel> {
    const userArray = [];
    for (const user of users) {
      const userModel = new UserModel(user);
      userArray.push(userModel);
    }
    return userArray;
  }

}
