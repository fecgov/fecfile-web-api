import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, ValidationErrors, Validators} from '@angular/forms';
import {UserModel} from './model/user.model';
import {ManageUserService} from './service/manage-user-service/manage-user.service';
import {DialogService} from '../../shared/services/DialogService/dialog.service';
import {ConfirmModalComponent, ModalHeaderClassEnum} from '../../shared/partials/confirm-modal/confirm-modal.component';
import {SortService} from './service/sort-service/sort.service';

export const roleDesc = {
  read_only: 'Can only view data, and cannot perform any other functions.',
  admin : 'Has all the access except managing users and Uploading',
  uploader : 'Can only view data, and upload',
  entry : 'Has access to enter, edit and delete information, but cannot upload reports or create other users.'
};

@Component({
  selector: 'app-manage-user',
  templateUrl: './manage-user.component.html',
  styleUrls: ['./manage-user.component.scss'],
  providers: [SortService]
})

export class ManageUserComponent implements OnInit {
  website = '';
  treasurerName = '';
  treasurerEmail = '';
  treasurerTel = '';
  treasurerFax = '';

  asstTreasurerName = '';
  asstTreasurerEmail = '';
  asstTreasurerTel = '';
  asstTreasurerFax = '';
  frmAddUser: FormGroup;
  users: Array<UserModel>;
  isEdit = false;
  currentEditUser: UserModel;
  _roleDesc = roleDesc;
  constructor(
      private _fb: FormBuilder,
      private _userService: ManageUserService,
      private _dialogService: DialogService,
      ) {
    this.frmAddUser = _fb.group({
      role: ['', Validators.required],
      first_name: ['', Validators.required],
      last_name: ['', Validators.required],
      contact: ['', [Validators.required, Validators.minLength(10)]],
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
    this.getFormValidationErrors();
    if (!this.frmAddUser.valid) {
      return;
    } else {
      this.frmAddUser.markAsTouched();
      this.frmAddUser.markAsDirty();
    }
    if (this.isEdit) {
    // do a put call
      const formData: any = {};
      for (const field in this.frmAddUser.controls) {
        formData[field] = this.frmAddUser.get(field).value;
      }
      const isActive = this.currentEditUser.isActive;
      const id = this.currentEditUser.id;
      formData['is_active'] = isActive;
      formData['id'] = id;
      this._userService.saveUser(formData, false).subscribe(res => {
        if (res) {
          console.log('SAVE SUCCESSFUL');
          this._dialogService.confirm(
              'The user has been updated successfully',
              ConfirmModalComponent,
              'User Updated',
              false,
              ModalHeaderClassEnum.successHeader);
          // reset form
          this.frmAddUser.reset();
          //refresh users list
          this.users = this.mapFromUserFields(res.users);
        }
      }, error => {
        console.log(error);
      });
    } else {
      const formData: any = {};
      for (const field in this.frmAddUser.controls) {
        formData[field] = this.frmAddUser.get(field).value;
      }
      // Account should be inactive by default
      // Backend should do email verification and make it active
      // TODO: Should not require to post is_active on creation
      formData['is_active'] = false;
      this._userService.saveUser(formData, true).subscribe(res => {
        if (res) {
          console.log('SAVE SUCCESSFUL');
          this._dialogService.confirm(
              'The user has been added successfully',
              ConfirmModalComponent,
              'User Added',
              false,
              ModalHeaderClassEnum.successHeader);
          // reset form
          this.frmAddUser.reset();
          //refresh users list
          this.users = this.mapFromUserFields(res.users);
        }
      },
          error => {
            console.log(error);
          });
    }
  }

  editUser(user: UserModel) {
    this.frmAddUser.reset();
    this.isEdit = true;
    this.frmAddUser.patchValue({ 'first_name': user.firstName }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'last_name': user.lastName }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'email': user.email }, { onlySelf: true });
    this.frmAddUser.patchValue({ 'contact': user.contact }, { onlySelf: true });
    this.frmAddUser.patchValue({'role': user.role}, {onlySelf: true});
    this.currentEditUser = user;
  }

  toggleStatus(user: UserModel) {
    const id = user.id;

    this._userService.toggleUser(id).subscribe(res => {
      if (res) {
        this.users = this.mapFromUserFields(res.users);
      }
    });
  }

  clearForm() {
    this.frmAddUser.reset();
    this.isEdit = false;
  }

  deleteUser(user: UserModel) {
    const id = user.id;
    const index = this.users.indexOf(user);
   this._userService.deleteUser(id).subscribe( res => {
     if (res) {
       this.users.splice(index, 1);
     }
   });
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
  protected getFormValidationErrors() {
    Object.keys(this.frmAddUser.controls).forEach(key => {
      const controlErrors: ValidationErrors = this.frmAddUser.get(key).errors;
      if (controlErrors != null) {
        Object.keys(controlErrors).forEach(keyError => {
          console.error('Key control: ' + key + ', keyError: ' + keyError + ', err value: ', controlErrors[keyError]);
        });
      }
    });
  }

  getSelectedRole(): string {
    if (this.frmAddUser.get('role').valid) {
      const role = this.frmAddUser.get('role').value.toLowerCase();
      const re = /\-/gi;
      const roleRe = role.replace(re, '_');
      return Object(this._roleDesc)[roleRe];
    }
    return '';
  }

  onSorted($event: any) {
    // TODO: revist sorting
    const sortColumn = $event.sortColumn;
    const sortDirection = $event.sortDirection;
    let sortedUsers;
    // if (columnName === 'lastName') {
    //   if (sortDirection === 'asc') {
    //     sortedUsers = this.users.sort((a, b) => a.lastName < b.lastName ? -1 : a.lastName > b.lastName ? 1 : 0);
    //   } else {
    //     sortedUsers = this.users.sort((a, b) => a.lastName < b.lastName ? -1 : a.lastName > b.lastName ? 1 : 0);
    //   }
    // }
    this.users = this.users.sort((a, b) => {
      if (sortDirection === 'desc') {
        if (a[sortColumn] < b[sortColumn]) {
          return -1;
        }
        if (a[sortColumn] > b[sortColumn]) {
          return 1;
        }
        return 0;
      } else {
        if (a[sortColumn] > b[sortColumn]) {
          return -1;
        }
        if (a[sortColumn] < b[sortColumn]) {
          return 1;
        }
        return 0;
      }
    });
  }
}
