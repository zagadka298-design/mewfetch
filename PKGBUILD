# Maintainer: zagadka298-design
pkgname=mewfetch
pkgver=2.0.0
pkgrel=1
pkgdesc="Lightweight system info fetch tool for Linux with ASCII cat art"
arch=('any')
url="https://github.com/zagadka298-design/mewfetch"
license=('MIT')
depends=('python')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/zagadka298-design/mewfetch/archive/refs/heads/main.tar.gz")
sha256sums=('837bbddbc6af055127e253130f6a6d2f73bdf87a8c882639809381e965e57f4e')

package() {
    cd "${srcdir}/mewfetch-main"

    # Устанавливаем скрипт в /usr/bin/mewfetch
    install -Dm755 mewfetch.py "${pkgdir}/usr/bin/mewfetch"
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
