/**
 * A model for validation errors.
 *
 * TODO move to shared onced discussed and agreed to use.
 */
export class ValidationErrorModel {

  public message: string;
  public isError: boolean;

  public constructor( message: string, isError: boolean) {
    this.message = message;
    this.isError = isError;
  }

}
