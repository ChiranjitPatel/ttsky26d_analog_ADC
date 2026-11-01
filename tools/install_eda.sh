#!/usr/bin/env bash
# Install the EDA tools and sky130 PDK at the same versions as the designer's PC,
# so cloud and local simulation results match.
#
#   Designer's PC (2026-11, Ubuntu 22.04):
#     open_pdks 1.0.577 (fc20c144), sky130_fd_pr 403964dc, PDK_ROOT=/usr/local/share/pdk
#     ngspice 36, xschem 3.4.8RC, magic 8.3.411, netgen 1.5.318, KLayout 0.30.8
#
# Usage:  sudo tools/install_eda.sh [step ...]
#   steps: deps magic netgen ngspice xschem klayout pdk   (default: all, in that order)
# Env:    PREFIX (default /usr/local), BUILD (default /opt/eda-build), JOBS (default nproc)
set -euo pipefail

PREFIX=${PREFIX:-/usr/local}
BUILD=${BUILD:-/opt/eda-build}
JOBS=${JOBS:-$(nproc)}
export PDK_ROOT=${PDK_ROOT:-$PREFIX/share/pdk}

MAGIC_TAG=8.3.411
NETGEN_TAG=1.5.318
OPEN_PDKS_COMMIT=fc20c144baf309002e0b335585a3aaef06b56f00   # open_pdks 1.0.577
NGSPICE_SRC=http://archive.ubuntu.com/ubuntu/pool/universe/n/ngspice/ngspice_36+ds.orig.tar.gz
NGSPICE_SHA256=""   # filled in after first verified download (see below)
XSCHEM_BEFORE=2026-04-25   # "3.4.8RC" = master between 3.4.7 and 3.4.8; pick master as of this date
KLAYOUT_VERSION=0.30.8

mkdir -p "$BUILD"
log() { printf '\n=== %s ===\n' "$*"; }

clone() {  # clone <url> <dir> <ref>
  local url=$1 dir=$2 ref=$3
  [ -d "$BUILD/$dir/.git" ] || git clone -q "$url" "$BUILD/$dir"
  git -C "$BUILD/$dir" fetch -q --tags origin || true
  git -C "$BUILD/$dir" checkout -q "$ref"
}

step_deps() {
  log deps
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    build-essential git m4 csh tcsh gawk bison flex autoconf automake libtool pkg-config \
    tcl-dev tk-dev libx11-dev libxpm-dev libxaw7-dev libxext-dev libxrender-dev libcairo2-dev \
    libreadline-dev libncurses-dev libfftw3-dev zlib1g-dev python3 python3-pip curl xvfb >/dev/null
}

step_magic() {
  log "magic $MAGIC_TAG"
  clone https://github.com/RTimothyEdwards/magic magic "$MAGIC_TAG"
  cd "$BUILD/magic"
  ./configure --prefix="$PREFIX" --without-opengl >/dev/null
  make -s -j"$JOBS" >/dev/null && make -s install >/dev/null
  magic --version
}

step_netgen() {
  log "netgen $NETGEN_TAG"
  clone https://github.com/RTimothyEdwards/netgen netgen "$NETGEN_TAG"
  cd "$BUILD/netgen"
  ./configure --prefix="$PREFIX" >/dev/null
  make -s -j"$JOBS" >/dev/null && make -s install >/dev/null
}

step_ngspice() {
  log "ngspice 36 (Ubuntu 22.04 source package)"
  cd "$BUILD"
  [ -f ngspice_36.orig.tar.gz ] || curl -sSfL "$NGSPICE_SRC" -o ngspice_36.orig.tar.gz
  if [ -n "$NGSPICE_SHA256" ]; then echo "$NGSPICE_SHA256  ngspice_36.orig.tar.gz" | sha256sum -c -; fi
  rm -rf ngspice-36 && mkdir ngspice-36 && tar -xzf ngspice_36.orig.tar.gz -C ngspice-36 --strip-components=1
  cd ngspice-36
  [ -x configure ] || ./autogen.sh >/dev/null
  ./configure --prefix="$PREFIX" --with-x --enable-xspice --enable-cider --enable-openmp \
    --with-readline=yes --disable-debug >/dev/null
  make -s -j"$JOBS" >/dev/null && make -s install >/dev/null
  ngspice -v | head -2
}

step_xschem() {
  log "xschem (master as of $XSCHEM_BEFORE)"
  clone https://github.com/StefanSchippers/xschem xschem master
  local rev; rev=$(git -C "$BUILD/xschem" rev-list -1 --before="$XSCHEM_BEFORE" origin/master)
  git -C "$BUILD/xschem" checkout -q "$rev"
  cd "$BUILD/xschem"
  ./configure --prefix="$PREFIX" >/dev/null
  make -s -j"$JOBS" >/dev/null && make -s install >/dev/null
  echo "xschem commit $rev"
}

step_klayout() {
  log "KLayout $KLAYOUT_VERSION (Python module; GUI/DRC binary is built separately if needed)"
  pip install -q --break-system-packages "klayout==$KLAYOUT_VERSION" 2>/dev/null \
    || pip install -q "klayout==$KLAYOUT_VERSION"
  python3 -c "import klayout.db as db; print('klayout python', db.__version__ if hasattr(db,'__version__') else 'ok')"
}

step_pdk() {
  log "open_pdks $OPEN_PDKS_COMMIT (sky130A, reference commits)"
  clone https://github.com/RTimothyEdwards/open_pdks open_pdks "$OPEN_PDKS_COMMIT"
  cd "$BUILD/open_pdks"
  ./configure --prefix="$PREFIX" --enable-sky130-pdk --with-sky130-variants=A --with-reference \
    --enable-primitive-sky130 --enable-io-sky130 --enable-sc-hd-sky130 \
    --enable-xschem-sky130 --enable-klayout-sky130 --enable-precheck-sky130 \
    --disable-sc-hs-sky130 --disable-sc-ms-sky130 --disable-sc-ls-sky130 --disable-sc-lp-sky130 \
    --disable-sc-hdll-sky130 --disable-sc-hvl-sky130 --disable-alpha-sky130 \
    --disable-sram-sky130 --disable-sram-space-sky130 --disable-reram-sky130 \
    --disable-osu-t12-sky130 --disable-osu-t15-sky130 --disable-osu-t18-sky130 >/dev/null
  make -j"$JOBS" >"$BUILD/open_pdks.log" 2>&1 || { tail -40 "$BUILD/open_pdks.log"; exit 1; }
  make install >>"$BUILD/open_pdks.log" 2>&1
  grep -A3 '"build"' "$PDK_ROOT/sky130A/.config/nodeinfo.json"
}

steps=("$@"); [ ${#steps[@]} -gt 0 ] || steps=(deps magic netgen ngspice xschem klayout pdk)
for s in "${steps[@]}"; do "step_$s"; done
log "done — PDK_ROOT=$PDK_ROOT"
