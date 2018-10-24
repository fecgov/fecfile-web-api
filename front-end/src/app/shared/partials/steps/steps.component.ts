import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-steps',
  templateUrl: './steps.component.html',
  styleUrls: ['./steps.component.scss']
})
export class StepsComponent implements OnInit {

  @Input() steps: any;
  @Input() current_step: any;

  constructor() { }

  ngOnInit(): void {}

}
