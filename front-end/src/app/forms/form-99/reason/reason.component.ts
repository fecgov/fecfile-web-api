import { Subscription } from 'rxjs/Subscription';
import {
  Component,
  EventEmitter,
  ElementRef,
  Input,
  OnInit,
  Output,
  Renderer2,
  ViewEncapsulation,
  ViewChild
, ChangeDetectionStrategy, 
OnDestroy} from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Observable } from 'rxjs';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { htmlLength } from '../../../shared/utils/forms/validation/html-length.validator';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { THIS_EXPR } from '@angular/compiler/src/output/output_ast';

@Component({
  selector: 'f99-reason',
  templateUrl: './reason.component.html',
  styleUrls: ['./reason.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReasonComponent implements OnInit , OnDestroy{
  
  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild('htmlEditor') htmlEditor: ElementRef;
  @ViewChild('fileInput') fileInput: ElementRef;

  public editMode: boolean;
  public reportId: number;
  public frmReason: FormGroup;
  public reasonType: string = null;
  public reasonFailed: boolean = false;
  public reasonHasInvalidHTML: boolean = false;
  public typeSelected: string = null;
  public lengthError: boolean = false;
  public isValidReason: boolean = false;
  public isFiled: boolean = false;
  public characterCount: number = 0;
  public formSaved: boolean = false;
  public hideText: boolean = false;
  public showValidateBar: boolean = false;
  public file: any = null;
  public notValidPdf: boolean = false;
  public validFile: boolean = true;
  public showFileDeleteButton: boolean = false;
  public notCorrectPdfSize: boolean = false;
  public closeResult: string = '';
  public PdfUploaded: boolean = false;
  public PdfDeleted: boolean = false;
  public editorMax: number = 20000;
  public textAreaTextContent: any = '';
  public editingTextArea: boolean = false;
  public fileNameToDisplay: string = null;
  public showFileNameLengthError: boolean = false;

  private committee_details: any = {};
  private _printPriviewPdfFileLink: string = '';
  private _form99Details: any = {};
  private _formType: string = '';
  private _formSaved: boolean = false;
  private _formSubmitted: boolean = false;
  private _reasonInnerText: string = ''; // The text, plus any HTML tags
  private _reasonInnerHTML: string = ''; // Shows the value and applys the HTML
  private _reasonTextContent: string = ''; // The plain text, no HTML from editor
  private _setRefresh: boolean = false;
  queryParamsSub: Subscription;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _formsService: FormsService,
    private _renderer: Renderer2,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _modalService: NgbModal,
    private _dormSanitizer: DomSanitizer
  ) {
    this._messageService.clearMessage();
    this.queryParamsSub = _activatedRoute.queryParams.subscribe(p => {
      if (p.refresh === true || p.refresh === 'true') {
        this._setRefresh = true;
        this.ngOnInit();
      }
      if (p.reportId) {
        this.reportId = p.reportId;
      }
    });
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.editMode = this._activatedRoute.snapshot.queryParams.edit === 'false' ? false : true;
    this._form99Details = JSON.parse(localStorage.getItem(`form_${this._formType}_details`));
    this.committee_details = JSON.parse(localStorage.getItem('committee_details'));

    if (this._form99Details) {
      if (!this._form99Details.id) {
        this.file = null;
      }
      if (this._form99Details.text) {
        if (this._form99Details.reason) {
          this.typeSelected = this._form99Details.reason;
          this.editingTextArea = true;
        }
        this.frmReason = this._fb.group({
          reasonText: [this._form99Details.text, [Validators.required, htmlLength(this.editorMax)]],
          file: ['']
        });
        const unescapedText = this._form99Details.text;
        this.frmReason.controls['reasonText'].setValue(unescapedText);
        this._reasonTextContent = unescapedText;
        this._reasonInnerText = unescapedText;
        this._reasonInnerHTML = unescape(unescapedText);
        this.textAreaTextContent = this._dormSanitizer.bypassSecurityTrustHtml(unescapedText);
        if (this._form99Details.filename) {
          this.fileNameToDisplay = this._form99Details.filename;
        } else if (localStorage.getItem('orm_99_details.org_filename')) {
          this.fileNameToDisplay = localStorage.getItem('orm_99_details.org_filename');
        }
      } else {
        this.editingTextArea = false;
        this.frmReason = this._fb.group({
          reasonText: ['', [Validators.required, htmlLength(this.editorMax)]],
          file: ['']
        });
        this.fileNameToDisplay = null;
      }
    } else {
      this.frmReason = this._fb.group({
        reasonText: ['', [Validators.required, htmlLength(this.editorMax)]],
        file: ['']
      });
      this.fileNameToDisplay = null;
    }
  }

  ngOnDestroy(): void {
    this.queryParamsSub.unsubscribe();
  }

  ngDoCheck(): void {
    let form_99_details: any = {};

    if (localStorage.getItem('form_99_details') !== null) {
      form_99_details = JSON.parse(localStorage.getItem('form_99_details'));
    }

    if (form_99_details) {
      this.typeSelected = form_99_details.reason;
    }

    if (this.frmReason.get('reasonText').value.length >= 1) {
      let text: string = this.frmReason.get('reasonText').value;
      this.characterCount = this._countCharacters(text);
    } else if (this.frmReason.get('reasonText').value.length === 0) {
      let text: string = this.frmReason.get('reasonText').value;
      this.characterCount = this._countCharacters(text);
    }
  }

  public reasonTextEmpty(): boolean {
    if (!this.frmReason.controls.reasonText.value.replace(/(\s)/g, '').length) {
      return true;
    }
    return false;
  }

  /**
   * Executed when a user types in text into the editor area.
   *
   * @param      {Object}  e       The event object.
   */
  public editorChange(e): void {
    if (this.editMode) {
      this._reasonTextContent = e.target.textContent;

      if (this._reasonTextContent.length >= 1) {
        this._reasonInnerText = e.target.innerText;

        if (this._checkUnsupportedHTML(this._reasonInnerText)) {
          this.reasonHasInvalidHTML = true;

          this.frmReason.controls['reasonText'].setValue('');
          this.frmReason.controls['reasonText'].markAsTouched();
          this.frmReason.controls['reasonText'].markAsDirty();
        } else {
          this.reasonHasInvalidHTML = false;

          if (!this._validateForSpaces(this._reasonInnerText)) {
            this._reasonInnerHTML = e.target.innerHTML;

            this.frmReason.controls['reasonText'].setValue(this._reasonInnerHTML);

            this.frmReason.controls['reasonText'].markAsTouched();
            this.frmReason.controls['reasonText'].markAsDirty();

            this.showValidateBar = false;
            this.reasonFailed = false;

            this.hideText = true;
            this.formSaved = false;

            this._messageService.sendMessage({
              validateMessage: {
                validate: {},
                showValidateBar: false
              }
            });
          } else {
            this.frmReason.controls['reasonText'].setValue('');
            this.frmReason.controls['reasonText'].markAsPristine();
            this.frmReason.controls['reasonText'].markAsUntouched();

            this._reasonInnerHTML = '';
            this._reasonInnerText = '';
            this._reasonTextContent = '';

            this.reasonFailed = true;
          }
        }
      } else {
        this.frmReason.controls['reasonText'].setValue('');
        this.frmReason.controls['reasonText'].markAsPristine();
        this.frmReason.controls['reasonText'].markAsUntouched();

        this.reasonHasInvalidHTML = false;

        this.reasonFailed = true;

        this._messageService.sendMessage({
          validateMessage: {
            validate: {},
            showValidateBar: false
          }
        });
      }
    }
  }

  private _setF99Details(): void {
    if (this.committee_details) {
      if (this.committee_details.committeeid) {
        this._form99Details = this.committee_details;

        this._form99Details.reason = '';
        this._form99Details.text = '';
        this._form99Details.signee = `${this.committee_details.treasurerfirstname} ${this.committee_details.treasurerlastname}`;
        this._form99Details.additional_email_1 = '-';
        this._form99Details.additional_email_2 = '-';
        this._form99Details.created_at = '';
        this._form99Details.is_submitted = false;
        this._form99Details.id = '';

        let formSavedObj: any = {
          saved: false
        };
        localStorage.setItem(`form_99_details`, JSON.stringify(this._form99Details));
        localStorage.setItem(`form_99_saved`, JSON.stringify(formSavedObj));
      }
    }
  }

  public checkIfEditMode() {
    if (!this.editMode) {
      this._dialogService
        .newReport(
          'This report has been filed with the FEC. If you want to change, you must file a new report.',
          ConfirmModalComponent,
          'Warning',
          true,
          false,
          true
        )
        .then(res => {
          if (res === 'cancel' || res === ModalDismissReasons.BACKDROP_CLICK || res === ModalDismissReasons.ESC) {
            // this.ngOnInit();
            this._dialogService.checkIfModalOpen();
          } else if (res === 'NewReport') {
            this.editMode = true;
            localStorage.removeItem('form_99_details');
            localStorage.removeItem('form_99_saved');
            this._setF99Details();
            setTimeout(() => {
              this._router.navigate(['/forms/form/99'], {
                queryParams: { step: 'step_1', edit: this.editMode, refresh: true }
              });
            }, 500);
          }
        });
    }
  }

  /**
   * Inserts HTML for button clicked in the toolbar.
   *
   * @param      {Object}  e       The event object.
   */
  public insertHTML(e: any): void {
    if (typeof e === 'object') {
      try {
        const htmlTagType: string = e.currentTarget.getAttribute('data-command');

        document.execCommand(htmlTagType, false, '');

        this.htmlEditor.nativeElement.focus();
      } catch (error) {
        //console.log('There was an error.');
        //console.log('error: ', error);
      }
    }
  }

  /**
   * Removes any HTML from pasted content into editor.
   *
   * @param      {Object}  e       The event object.
   */
  public removeHTML(e: any): void {
    e.preventDefault();

    if (typeof e === 'object') {
      try {
        const plainText: string = e.clipboardData.getData('text/plain');

        window.document.execCommand('insertHTML', false, plainText);
      } catch (error) {
        //console.log('error: ', error);
      }
    }
  }

  /**
   * Counts the number of characters in the editor.
   *
   * @param      {string}  text    The text
   * @return     {number}  Number of characters.
   */
  private _countCharacters(text: string): number {
    const regex: any = /((<(\/?|\!?)\w+>)|(<\w+.*?\w="(.*?)")>|(<\w*.*\/>))/gm;
    let characterCount: number = text.replace(regex, '').length || 0;

    return characterCount;
  }

  /**
   * Validates text area for just spaces or new line characters entered.
   *
   * @param      {string}   text    <ifrThe text.
   * @return     {boolean}  The result.
   */
  private _validateForSpaces(text: string): boolean {
    const regex: any = /^\s*$/;

    if (regex.test(text)) {
      return true;
    }

    return false;
  }

  /**
   * Checks for unsupported markup in reason text.
   *
   * @param      {string}   text    The text.
   * @return     {boolean}  Indicates if there is invalid markup or not.
   */
  private _checkUnsupportedHTML(text: string): boolean {
    const hasHTMLTags: any = /((<(\/?|\!?)\w+>)|(<\w+.*?\w="(.*?)")>|(<\w*.*\/>))/gm;

    if (hasHTMLTags.test(text)) {
      const htmlTagsWhiteList: any = /(<(\/?|\!?)(html|head|body|script|script.*?src="(.*?)"|iframe|iframe.*?src="(.*?)"|link|style|table|thead|tbody|th|tr|td|img|img.*?src="(.*?)"|fieldset|form|input|textarea|select|option|a|a.*?href="(.*?)"|progress|noscript|audio|video)(\s*\/*)>)/gm;

      if (htmlTagsWhiteList.test(text)) {
        return true;
      } else {
        return false;
      }
    }

    return false;
  }

  /**
   * Toggles a tooltip.
   *
   * @param      {<type>}  tooltip  The tooltip
   */
  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }

  public removeFile(modalId: string): void {
    this._modalService.open(modalId);
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.hideText = true;
    this.formSaved = false;

    this.showValidateBar = false;

    this._messageService.sendMessage({
      validateMessage: {
        validate: {},
        showValidateBar: false
      }
    });

    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_1',
      edit: this.editMode
    });
  }

  public setFile(e): void {
    if (!this.editMode) {
      this.checkIfEditMode();
    } else if (e.target.files.length === 1 && this.editMode && e.target.files[0].name.length <= 100) {
      this.file = e.target.files[0];
      if (this.file.name.includes('.pdf')) {
        let fileNameObj: any = {
          fileName: this.file.name
        };

        if (this.file.size > 33554432) {
          this.notCorrectPdfSize = true;
        } else {
          this.notCorrectPdfSize = false;
        }
        localStorage.setItem(`form_${this._formType}_file`, JSON.stringify(fileNameObj));
        this.showFileNameLengthError = false;
        this.notValidPdf = false;
        this.validFile = true;
        this.showFileDeleteButton = true;
        this._form99Details.filename = this.file.name;
        this.PdfUploaded = true;
        this.PdfDeleted = false;
      } else {
        this.notValidPdf = true;
        this.validFile = false;
        this.file = null;
        this.notCorrectPdfSize = false;
        this.PdfUploaded = false;
      }
    } else if (e.target.files[0].name.length > 100) {
      this.showFileNameLengthError = true;
      let fileNameObj: any = {
        fileName: ''
      };
      localStorage.setItem(`form_${this._formType}_file`, JSON.stringify(fileNameObj));
      this.validFile = false;
      this.file = null;
      this.showFileDeleteButton = false;
      this.fileInput.nativeElement.value = '';
      this._form99Details.filename = '';
      this.PdfUploaded = false;
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
      window.scrollTo(0, 0);
    } else {
      let fileNameObj: any = {
        fileName: ''
      };
      localStorage.setItem(`form_${this._formType}_file`, JSON.stringify(fileNameObj));
      this.notValidPdf = true;
      this.validFile = false;
      this.file = null;
      this.showFileDeleteButton = false;
      this.fileInput.nativeElement.value = '';
      this._form99Details.filename = '';
      this.PdfUploaded = false;
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
    }
  }

  /**
   * Validates the reason form.
   *
   */
  public doValidateReason() {
    if (this.editMode) {
      if (this.frmReason.valid) {
        if (this._reasonTextContent.length >= 1) {
          if (!this._checkUnsupportedHTML(this._reasonInnerText)) {
            if (!this._validateForSpaces(this._reasonInnerText)) {
              let formSaved: any = {
                form_saved: this.formSaved
              };
              this.reasonFailed = false;
              this.isValidReason = true;

              this._form99Details = JSON.parse(localStorage.getItem(`form_${this._formType}_details`));
              this._form99Details.text = this._reasonInnerHTML;

              window.localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));

              window.localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(formSaved));

              this.saveForm();

              this.hideText = true;

              this.showValidateBar = false;

              this.hideText = true;
              this.formSaved = false;

              this._messageService.sendMessage({
                validateMessage: {
                  validate: '',
                  showValidateBar: false
                }
              });

              this.status.emit({
                form: this.frmReason,
                direction: 'next',
                step: 'step_3',
                previousStep: 'step_2',
                edit: this.editMode,
                refresh: this._setRefresh
              });

              this._messageService.sendMessage({
                data: this._form99Details,
                previousStep: 'step_3'
              });
            } else {
              this.reasonFailed = true;

              window.scrollTo(0, 0);
            } // !this._validateForSpaces
          } else {
            this.reasonHasInvalidHTML = true;

            this.frmReason.controls['reasonText'].setValue('');

            window.scrollTo(0, 0);
          } // !this._checkUnsupportedHTML
        } else {
          this.reasonFailed = true;
          this.isValidReason = false;

          this.frmReason.controls['reasonText'].setValue('');
          this.frmReason.controls['reasonText'].markAsPristine();
          this.frmReason.controls['reasonText'].markAsUntouched();
          this.frmReason.setErrors({ incorrect: true });

          this.status.emit({
            form: this.frmReason,
            direction: 'next',
            step: 'step_2',
            edit: this.editMode,
            previousStep: ''
          });

          window.scrollTo(0, 0);
          return;
        } // this.reasonTextArea.length
      } else {
        this.reasonFailed = true;
        this.isValidReason = false;
        this.frmReason.setErrors({ incorrect: true });

        this.frmReason.controls['reasonText'].setValue('');
        this.frmReason.controls['reasonText'].markAsTouched();
        this.frmReason.controls['reasonText'].markAsDirty();

        window.scrollTo(0, 0);
        return;
      } // this.frmReason.valid
    } else {
      this.status.emit({
        form: this.frmReason,
        direction: 'next',
        step: 'step_3',
        previousStep: 'step_2',
        edit: this.editMode,
        refresh: this._setRefresh
      });
    }
  }

  /**
   * Saves the form when the save button is clicked.
   *
   */
  public saveForm() {
    if (this.frmReason.valid && this.editMode) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

        this._form99Details.text = this._reasonInnerHTML;

        this._form99Details.file = '';

        if (this.file !== null) {
          this._form99Details.file = this.file;
          this._form99Details.filename = this.file.name;
        }

        if (!this._form99Details.id) {
          this._form99Details.id = this.reportId;
        }
        localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

        this.hideText = true;

        this.showValidateBar = false;

        if ((this.PdfUploaded && typeof this.file === 'object') ||
        this.PdfDeleted ||
        (!this._form99Details.id || this._form99Details.id === '')) {
          this._formsService.saveForm({}, this.file, this._formType).subscribe(
            res => {
              if (res) {
                this._form99Details.id = res.id;
                this._router.navigate([],{relativeTo:this._activatedRoute, queryParams: {reportId: this._form99Details.id}, queryParamsHandling:'merge'});
                this._messageService.sendMessage({action:'updateForm99ReportId', reportId: this._form99Details.id});
                if (!res.file) {
                  localStorage.removeItem('orm_99_details.org_fileurl');
                } else if (res.file && (Object.entries(res.file).length || res.file !== '')) {
                  this.file = res.file;
                }

                localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

                // success
                this.formSaved = true;

                let formSavedObj: any = {
                  saved: this.formSaved
                };
                localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );
        } else {
          this._formsService.Signee_SaveForm({}, this._formType).subscribe(
            res => {
              if (res) {
                this._form99Details.id = res.id;

                localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));
                localStorage.setItem('orm_99_details.org_fileurl', res.file);

                // success
                this.formSaved = true;

                let formSavedObj: any = {
                  saved: this.formSaved
                };
                localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );
        }
      }
    }
  }

  /**
   * Validates the entire form.
   */
  public validateForm(): void {
    let type: string = localStorage.getItem('form99-type');

    this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

    this._form99Details.text = this.frmReason.controls['reasonText'].value;

    window.localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

    this.showValidateBar = true;

    this._formsService.validateForm({}, this._formType).subscribe(
      res => {
        if (res) {
          this._messageService.sendMessage({
            validateMessage: {
              validate: environment.validateSuccess,
              showValidateBar: true
            }
          });
        }
      },
      error => {
        this._messageService.sendMessage({
          validateMessage: {
            validate: error.error,
            showValidateBar: true
          }
        });
      }
    );
  }

  public printPreview() {
    if (this.frmReason.valid) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

        this._form99Details.text = this._reasonInnerHTML;

        this._form99Details.file = '';

        if (this.file !== null) {
          this._form99Details.file = this.file;
          this._form99Details.filename = this.file.name;
        }

        localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

        this.hideText = true;

        this.showValidateBar = false;

        if (this.file !== null) {
          this._formsService.PreviewForm_ReasonScreen({}, this.file, this._formType).subscribe(
            res => {
              if (res) {
                this._form99Details.id = res.id;
                localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));
                // success
                this.formSaved = true;
                let formSavedObj: any = {
                  saved: this.formSaved
                };
                localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
                window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );
        } else {
          this._formsService.PreviewForm_Preview_sign_Screen({}, '99').subscribe(
            res => {
              if (res) {
                this._form99Details.id = res.id;
                localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));
                // success
                this.formSaved = true;
                let formSavedObj: any = {
                  saved: this.formSaved
                };
                localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
                window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
              }
            },
            error => {
              //console.log('error: ', error);
            }
          );
        }
      }
    }
  }
  public deletePDF(message: string, modalId: string): void {
    if (message === 'Yes') {
      this.file = null;
      this.notValidPdf = false;

      this._form99Details.filename = '';
      this.fileNameToDisplay = null;
      localStorage.removeItem('orm_99_details.org_filename');
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
    }
    //this._modalService.close(modalId);
  }

  public open(content): void {
    this._modalService.open(content, { ariaLabelledBy: 'modal-basic-title' }).result.then(
      result => {
        this.closeResult = `Closed with: ${result}`;
      },
      reason => {
        this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
      }
    );
  }

  private _getDismissReason(reason: any): string {
    if (reason === 'OK click') {
      this.PdfDeleted = true;
      this.file = null;
      this.notValidPdf = false;
      this.PdfUploaded = false;
      this._form99Details.filename = '';
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
    } else if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return `with: ${reason}`;
    }
  }

  public deletePDFFile() {
    this._dialogService
      .confirm('Do you want to delete uploaded pdf file?', ConfirmModalComponent, 'Delete PDF File', true)
      //.reportExist(alertStr, ConfirmModalComponent,'Report already exists' ,true,false,true)
      .then(res => {
        if (res === 'cancel') {
          /*this.optionFailed = true;
       this.isValidType = false;
       window.scrollTo(0, 0);
       this.status.emit({
         form: {},
         direction: 'previous',
         step: 'step_1'
       });*/

          return 0;
        } else if (res === 'okay') {
          this.PdfDeleted = true;
          this.file = null;
          this.notValidPdf = false;
          this.PdfUploaded = false;
          this._form99Details.filename = '';
          this.fileNameToDisplay = null;
          localStorage.removeItem('orm_99_details.org_filename');
          localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
        }
      });
  }
}
