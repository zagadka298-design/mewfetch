# Maintainer: zagadka298-design
pkgname=mewfetch
pkgver=2.1.0
pkgrel=1
pkgdesc="Lightweight system info fetch tool for Linux with ASCII cat art"
arch=('any')
url="https://github.com/zagadka298-design/mewfetch"
license=('MIT')
depends=('python')
makedepends=('python-build' 'python-installer' 'python-setuptools' 'python-wheel')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/zagadka298-design/mewfetch/archive/refs/heads/main.tar.gz")
sha256sums=('SKIP')

build() {
    cd "${srcdir}/mewfetch-main"
    python -m build --wheel --no-isolation
}

package() {
    cd "${srcdir}/mewfetch-main"
    python -m installer --destdir="${pkgdir}" dist/*.whl
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
