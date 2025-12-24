import { FileSystemIconLoader } from '@iconify/utils/lib/loader/node-loaders'
import presetIcons from '@unocss/preset-icons'
import {
  defineConfig,
  presetAttributify,
  presetTypography,
  presetWind3,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'
import presetChinese from 'unocss-preset-chinese'
import presetEase from 'unocss-preset-ease'

export default defineConfig({
  safelist: [
    'py-16px',
    'pb-16px',
  ],
  presets: [
    presetWind3(),
    presetAttributify(),
    presetChinese(),
    presetEase(),
    presetTypography(),
    presetIcons({
      // scale: 1.2,
      warn: true,
      extraProperties: {
        display: 'inline-block',
      },
      collections: {
        light: FileSystemIconLoader(
          './src/assets/icons/svg/light',
          svg => svg.replace(/#000/g, 'currentColor'),
        ),
        dark: FileSystemIconLoader(
          './src/assets/icons/svg/dark',
          svg => svg.replace(/#000/g, 'currentColor'),
        ),
      },
      customizations: {
        iconCustomizer(collection, icon, props) {
          if (collection === 'light' || collection === 'dark') {
            props.width = '1em'
            props.height = '1em'
          }
        },
      },
    }),
  ],
  shortcuts: [
    ['flex-center', 'flex items-center justify-center'],
    ['flex-between', 'flex items-center justify-between'],
    ['flex-end', 'flex items-end justify-between'],
  ],
  transformers: [transformerDirectives(), transformerVariantGroup()],
})
