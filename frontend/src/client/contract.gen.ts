import type { z } from "zod"
import type * as Types from "./types.gen"
import type * as Schemas from "./zod.gen"

type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false
type Expect<T extends true> = T
type Matches<S extends z.ZodType, T> = Same<z.input<S>, T>

export type ContractTypes = [
  Expect<Matches<typeof Schemas.zAccountDeletion, Types.AccountDeletion>>,
  Expect<Matches<typeof Schemas.zCredentials, Types.Credentials>>,
  Expect<Matches<typeof Schemas.zEmailChange, Types.EmailChange>>,
  Expect<Matches<typeof Schemas.zEmailChangeConfirm, Types.EmailChangeConfirm>>,
  Expect<Matches<typeof Schemas.zHttpError, Types.HttpError>>,
  Expect<Matches<typeof Schemas.zHttpValidationError, Types.HttpValidationError>>,
  Expect<Matches<typeof Schemas.zItemCreate, Types.ItemCreate>>,
  Expect<Matches<typeof Schemas.zItemPublic, Types.ItemPublic>>,
  Expect<Matches<typeof Schemas.zItemUpdate, Types.ItemUpdate>>,
  Expect<Matches<typeof Schemas.zItemsPublic, Types.ItemsPublic>>,
  Expect<Matches<typeof Schemas.zMessage, Types.Message>>,
  Expect<Matches<typeof Schemas.zNewPassword, Types.NewPassword>>,
  Expect<Matches<typeof Schemas.zPasswordRecovery, Types.PasswordRecovery>>,
  Expect<Matches<typeof Schemas.zToken, Types.Token>>,
  Expect<Matches<typeof Schemas.zUpdatePassword, Types.UpdatePassword>>,
  Expect<Matches<typeof Schemas.zUserPublic, Types.UserPublic>>,
  Expect<Matches<typeof Schemas.zUserRegister, Types.UserRegister>>,
  Expect<Matches<typeof Schemas.zUserUpdateMe, Types.UserUpdateMe>>,
  Expect<Matches<typeof Schemas.zValidationError, Types.ValidationError>>,
]
