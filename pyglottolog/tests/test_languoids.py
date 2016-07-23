# coding: utf8
from __future__ import unicode_literals
from unittest import TestCase

from clldutils.testing import WithTempDir
from clldutils import jsonlib

from pyglottolog.tests.util import WithTree


class TestGlottocodes(WithTempDir):
    def test_Glottocodes(self):
        from pyglottolog.languoids import Glottocodes

        languoids = self.tmp_path('languoids')
        languoids.mkdir()
        jsonlib.dump({}, languoids.joinpath('glottocodes.json'))

        glottocodes = Glottocodes(repos=self.tmp_path())
        gc = glottocodes.new('abcd', dry_run=True)
        self.assertNotIn(gc, glottocodes)
        gc = glottocodes.new('abcd')
        self.assertIn(gc, glottocodes)
        # make sure it's also written to file:
        self.assertIn(gc, Glottocodes(repos=self.tmp_path()))


class TestGlottocode(TestCase):
    def test_glottocode_from_name(self):
        from pyglottolog.languoids import Glottocode, Glottocodes

        gc = Glottocode.from_name('a', dry_run=True)
        # only a dry-run, so not really added to glottocodes:
        self.assertNotIn(gc, Glottocodes())
        self.assertEqual(gc.split()[0], 'aaaa')

    def test_pattern(self):
        from pyglottolog.languoids import Glottocode

        pattern = Glottocode.pattern
        for valid in [
            'abcd1234',
            'a12d3456',
        ]:
            self.assertIsNotNone(pattern.match(valid))

        for invalid in [
            'abcd123',
            '12d3456',
            'aNOCODE',
            'NOCODE_abd',
            'nocode',
        ]:
            self.assertIsNone(pattern.match(invalid))

    def test_init(self):
        from pyglottolog.languoids import Glottocode

        with self.assertRaises(ValueError):
            Glottocode('a2')


class TestLanguoid(WithTree):
    def test_factory(self):
        from pyglottolog.languoids import Languoid, Level

        f = Languoid.from_dir(self.tree.joinpath('abcd1234'))
        l = Languoid.from_dir(self.tree.joinpath(f.id, 'abcd1235'))
        self.assertEqual(l.name, 'language')
        self.assertEqual(l.level, Level.language)
        self.assertAlmostEqual(l.latitude, 0.5)
        self.assertAlmostEqual(l.longitude, 0.5)
        self.assertEqual(l.id, 'abcd1235')
        self.assertEqual(l.macroareas, ['a', 'b'])
        self.assertEqual(l.parent, f)
        self.assertEqual(f.children[0], l)
        self.assertEqual(l.children[0].family, f)

    def test_attrs(self):
        from pyglottolog.languoids import Languoid, Level

        l = Languoid.from_name_id_level('name', 'abcd1235', Level.language)
        l.name = 'other'
        self.assertEqual(l.name, 'other')
        with self.assertRaises(ValueError):
            l.glottocode = 'x'
        with self.assertRaises(ValueError):
            l.id = 'x'
        self.assertEqual(l.id, l.glottocode)
        self.assertIsNone(l.hid)

    def test_make_index(self):
        from pyglottolog.languoids import make_index, Level

        for level in Level:
            res = make_index(level, repos=self.tmp_path())
            self.assertEqual(len(res), 2)
            self.assertTrue(all(p.exists() for p in res))

    def test_find_languoid(self):
        from pyglottolog.languoids import find_languoid

        self.assertEqual(
            find_languoid(tree=self.tree, glottocode='abcd1234').name, 'family')

    def test_walk_tree(self):
        from pyglottolog.languoids import walk_tree

        self.assertEqual(len(list(walk_tree(tree=self.tree))), 3)

    def test_macro_area_from_hid(self):
        from pyglottolog.languoids import macro_area_from_hid

        res = macro_area_from_hid(tree=self.tree)
        self.assertEqual(res['abc'], 'a')