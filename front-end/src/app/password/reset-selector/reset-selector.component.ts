import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-reset-selector',
  templateUrl: './reset-selector.component.html',
  styleUrls: ['./reset-selector.component.scss']
})
export class ResetSelectorComponent implements OnInit {
  frmUserInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder
  ) {
    this.frmUserInfo = _fb.group({
      resetOption: ['', Validators.required],
      committeeID: ['', Validators.required],
      personalKey: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', Validators.required]
    });
  }

  ngOnInit() {
  }

  back() {
    this.router.navigate(['/reset-password']).then(r => {
      // do nothing
    });
  }

  clearForm() {
    this.frmUserInfo.reset();
  }

  submit() {
    // TODO: submit the form and do not navigate anywhere
    // Check requirements
    // for now navigate to create password screen until service is ready
    // if (this.frmUserInfo.valid) {
    if (true) {
      this.router.navigate(['/create-password']).then(r => {
        // handle it
      });
    } /*else {
      this.frmUserInfo.markAsTouched();
    }*/
  }
  handleOptionChange() {
    // Handle the validator change when option changes
    // remove unwanted validators
  }
}
