import { BANK_NAME, PRODUCT_NAME } from '../../data/crm'
import logoMark from '../../assets/logo-mark.png'
import { cx } from '../../utils/cx'
import { Eyebrow } from '../atoms/Eyebrow'
import { Image } from '../atoms/Image'

export function BrandMark({ inverse = false, showProduct = true, className }) {
  return (
    <div className={cx('brand', inverse && 'brand--inverse', className)}>
      <Image className="brand-mark" src={logoMark} alt="" />
      <div>
        <Eyebrow inverse={inverse}>{BANK_NAME}</Eyebrow>
        {showProduct ? <p className="brand-name">{PRODUCT_NAME}</p> : null}
      </div>
    </div>
  )
}
