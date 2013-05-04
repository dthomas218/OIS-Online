# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: language.py 7620 2007-11-07 16:55:47Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor

langs = [
    ('', 'Language neutral (site default)'),
    ('aa', 'Afar'),
    ('ab', 'Abkhazian'),
    ('af', 'Afrikaans'),
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('as', 'Assamese'),
    ('ay', 'Aymara'),
    ('az', 'Azerbaijani'),
    ('ba', 'Bashkir'),
    ('be', 'Byelorussian (Belarussian)'),
    ('bg', 'Bulgarian'),
    ('bh', 'Bihari'),
    ('bi', 'Bislama'),
    ('bn', 'Bengali'),
    ('bo', 'Tibetan'),
    ('br', 'Breton'),
    ('ca', 'Catalan'),
    ('co', 'Corsican'),
    ('cs', 'Czech'),
    ('cy', 'Welsh'),
    ('da', 'Danish'),
    ('de', 'German'),
    ('dz', 'Bhutani'),
    ('el', 'Greek'),
    ('en', 'English'),
    ('eo', 'Esperanto'),
    ('es', 'Spanish'),
    ('et', 'Estonian'),
    ('eu', 'Basque'),
    ('fa', 'Persian'),
    ('fi', 'Finnish'),
    ('fj', 'Fiji'),
    ('fo', 'Faroese'),
    ('fr', 'French'),
    ('fy', 'Frisian'),
    ('ga', 'Irish (Irish Gaelic)'),
    ('gd', 'Scots Gaelic (Scottish Gaelic)'),
    ('gl', 'Galician'),
    ('gn', 'Guarani'),
    ('gu', 'Gujarati'),
    ('gv', 'Manx Gaelic'),
    ('ha', 'Hausa'),
    ('he', 'Hebrew'),
    ('hi', 'Hindi'),
    ('hr', 'Croatian'),
    ('hu', 'Hungarian'),
    ('hy', 'Armenian'),
    ('ia', 'Interlingua'),
    ('id', 'Indonesian'),
    ('ie', 'Interlingue'),
    ('ik', 'Inupiak'),
    ('is', 'Icelandic'),
    ('it', 'Italian'),
    ('iu', 'Inuktitut'),
    ('ja', 'Japanese'),
    ('jw', 'Javanese'),
    ('ka', 'Georgian'),
    ('kk', 'Kazakh'),
    ('kl', 'Greenlandic'),
    ('km', 'Cambodian'),
    ('kn', 'Kannada'),
    ('ko', 'Korean'),
    ('ks', 'Kashmiri'),
    ('ku', 'Kurdish'),
    ('kw', 'Cornish'),
    ('ky', 'Kirghiz'),
    ('la', 'Latin'),
    ('lb', 'Luxemburgish'),
    ('ln', 'Lingala'),
    ('lo', 'Laotian'),
    ('lt', 'Lithuanian'),
    ('lv', 'Latvian Lettish'),
    ('mg', 'Malagasy'),
    ('mi', 'Maori'),
    ('mk', 'Macedonian'),
    ('ml', 'Malayalam'),
    ('mn', 'Mongolian'),
    ('mo', 'Moldavian'),
    ('mr', 'Marathi'),
    ('ms', 'Malay'),
    ('mt', 'Maltese'),
    ('my', 'Burmese'),
    ('na', 'Nauru'),
    ('ne', 'Nepali'),
    ('nl', 'Dutch'),
    ('no', 'Norwegian'),
    ('oc', 'Occitan'),
    ('om', 'Oromo'),
    ('or', 'Oriya'),
    ('pa', 'Punjabi'),
    ('pl', 'Polish'),
    ('ps', 'Pashto'),
    ('pt', 'Portuguese'),
    ('qu', 'Quechua'),
    ('rm', 'Rhaeto-Romance'),
    ('rn', 'Kirundi'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('rw', 'Kiyarwanda'),
    ('sa', 'Sanskrit'),
    ('sd', 'Sindhi'),
    ('se', 'Northern S&aacute;mi'),
    ('sg', 'Sangho'),
    ('sh', 'Serbo-Croatian'),
    ('si', 'Singhalese'),
    ('sk', 'Slovak'),
    ('sl', 'Slovenian'),
    ('sm', 'Samoan'),
    ('sn', 'Shona'),
    ('so', 'Somali'),
    ('sq', 'Albanian'),
    ('sr', 'Serbian'),
    ('ss', 'Siswati'),
    ('st', 'Sesotho'),
    ('su', 'Sudanese'),
    ('sv', 'Swedish'),
    ('sw', 'Swahili'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('tg', 'Tajik'),
    ('th', 'Thai'),
    ('ti', 'Tigrinya'),
    ('tk', 'Turkmen'),
    ('tl', 'Tagalog'),
    ('tn', 'Setswana'),
    ('to', 'Tonga'),
    ('tr', 'Turkish'),
    ('ts', 'Tsonga'),
    ('tt', 'Tatar'),
    ('tw', 'Twi'),
    ('ug', 'Uigur'),
    ('uk', 'Ukrainian'),
    ('ur', 'Urdu'),
    ('uz', 'Uzbek'),
    ('vi', 'Vietnamese'),
    ('vo', 'Volap&uuml;k'),
    ('wo', 'Wolof'),
    ('xh', 'Xhosa'),
    ('yi', 'Yiddish'),
    ('yo', 'Yorouba'),
    ('za', 'Zhuang'),
    ('zh', 'Chinese'),
    ('zu', 'Zulu')
]
langs.sort(lambda x,y:cmp(x[1], y[1]))

class Language(VocabularyProvider):
    """ Available languages for a content object """

    id = 'language'
    ns = 'http://cmf.zope.org/propsets/dublincore'
    propid = 'language'

    def getValueFor(self, context):
        res = []
        for value, label in langs:
            data = {'label':label,
                    'value':value
                    }
            res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Language)

manage_addLanguage = Constructor(Language)
