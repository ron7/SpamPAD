"""Functional tests the FreeMail Plugin"""

from __future__ import absolute_import
import unittest
import tests.util

# Load FreeMail plugin and report SCORE and matching RULES
PRE_CONFIG = """loadplugin Mail::SpamAssassin::Plugin::FreeMail
report _SCORE_
report _TESTS_
"""

# Define rules used for testing
CONFIG = """
header CHECK_FREEMAIL_FROM                 eval:check_freemail_from()
header CHECK_FREEMAIL_FROM_REGEX           eval:check_freemail_from('\d@')

header CHECK_FREEMAIL_BODY                 eval:check_freemail_body()
header CHECK_FREEMAIL_BODY_REGEX           eval:check_freemail_body('\d@')

header CHECK_FREEMAIL_HEADER               eval:check_freemail_header('From')
header CHECK_FREEMAIL_HEADER_REGEX         eval:check_freemail_header('From', '\d@')

header CHECK_FREEMAIL_REPLY_TO eval:check_freemail_replyto('replyto')
header CHECK_FREEMAIL_REPLY eval:check_freemail_replyto('reply')

header CHECK_FREEMAIL_HEADER_CUSTOM        eval:check_freemail_header('Custom')
header CHECK_FREEMAIL_HEADER_CUSTOM_REGEX  eval:check_freemail_header('Custom', '\d@')

util_rb_tld com
"""

class TestFunctionalFreeMail(tests.util.TestBase):
    """Class containing functional tests for the FreeMail Plugin"""

    # Test check_freemail_from(), check_freemail_body() and check_freemail_header() eval rules

    def test_check_freemail_match_domain(self):
        """sender@example.com should match example.com freemail domain"""
        lists = """freemail_domains example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_match_wild_domain(self):
        """sender@example.com should match ex*.c?m freemail domain globbing
        expression"""
        lists = """freemail_domains ex*.c?m"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_dont_match_domain(self):
        """sender@example.com should not match example.net freemail domain"""
        lists = """freemail_domains example.net"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_dont_match_email(self):
        """sender@example.com should not match sender@example.com freemail domain"""
        lists = """freemail_domains sender@example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_match_regex(self):
        """sender1@example.com should match \d@ regex and also example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """From: sender1@example.com
        \nBody contains sender1@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 6, ['CHECK_FREEMAIL_BODY', 'CHECK_FREEMAIL_HEADER',
            'CHECK_FREEMAIL_FROM_REGEX', 'CHECK_FREEMAIL_BODY_REGEX',
            'CHECK_FREEMAIL_HEADER_REGEX', 'CHECK_FREEMAIL_FROM'])

    def test_check_freemail_match_with_empty_freemail_domains(self):
        """sender1@example.com should not match any rule if freemail_domains
        list is empty also should not match regex rule"""
        lists = """freemail_domains"""

        email = """From: sender1@example.com
        \nBody contains sender1@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_match_with_no_freemail_domains(self):
        """sender@example.com should not match any rule if freemail_domains
        list is not defined"""
        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_match_with_multi_freemail_domains(self):
        """sender@example.com should match example.com freemail domain if list
        also contains other domains"""
        lists = """freemail_domains example.net example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_match_with_split_freemail_domains(self):
        """sender@example.com should match example.com freemail domain if list
        also contains other domains splitted on multiple lines"""
        lists = """freemail_domains example.net
        freemail_domains example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_dont_match_if_email_is_in_default_whitelist(self):
        """abuse|support|sales|info|helpdesk|contact|kontakt@example.com
        should not match any rule because is on default whitelist"""
        lists = """freemail_domains example.com"""

        email = """From: abuse@example.com
        \nBody contains support@example.com sales@example.com contact@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_dont_match_if_domain_in_freemail_whitelist(self):
        """sender@example.com should not match example.com freemail domain if
        example.com exist in freemail_whitelist"""
        lists = """freemail_domains example.com
        freemail_whitelist example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_dont_match_if_email_in_freemail_whitelist(self):
        """sender@example.com should not match example.com freemail domain if
        sender@example.com exist in freemail_whitelist"""
        lists = """freemail_domains example.com
        freemail_whitelist sender@example.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_match_if_empty_freemail_whitelist(self):
        """sender@example.com should match example.com freemail domain if
        freemail_whitelist is empty"""
        lists = """freemail_domains example.com
        freemail_whitelist"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_match_if_wildcard_in_freemail_whitelist(self):
        """sender@example.com should match example.com freemail domain if
        *@example.com (wildcard value) exist in freemail_whitelist"""
        lists = """freemail_domains example.com
        freemail_whitelist *@exam?le.com"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_match_if_invalid_in_freemail_whitelist(self):
        """sender@example.com should match example.com freemail domain if
        example (invalid value) exist in freemail_whitelist"""
        lists = """freemail_domains example.com
        freemail_whitelist example"""

        email = """From: sender@example.com
        \nBody contains sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 3, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_BODY',
            'CHECK_FREEMAIL_HEADER'])

    def test_check_freemail_header_match_custom_header(self):
        """sender1@example.com should match example.com freemail domain for
        custom header"""
        lists = """freemail_domains example.com"""

        email = """Custom: sender1@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 2, ['CHECK_FREEMAIL_HEADER_CUSTOM',
            'CHECK_FREEMAIL_HEADER_CUSTOM_REGEX'])


    # Test check_freemail_from() eval rule for all from headers

    def test_check_freemail_from_match_on_resent_from_header(self):
        """sender@example.com on Resent-From header should match example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """Resent-From: sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_FROM'])

    def test_check_freemail_from_match_on_envelope_sender_header(self):
        """sender@example.com on Envelope-Sender header should match example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """Envelope-Sender: sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_FROM'])

    def test_check_freemail_from_match_on_resent_sender_header(self):
        """sender@example.com on Resent-Sender header should match example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """Resent-Sender: sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_FROM'])

    def test_check_freemail_from_match_on_x_envelope_from_header(self):
        """sender@example.com on X-Envelope-From: header should match example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """X-Envelope-From: sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_FROM'])

    def test_check_freemail_from_match_on_envelope_from_from_header(self):
        """sender@example.com on Reeived header in envelope-from should match example.com
        freemail domain"""
        lists = """freemail_domains spamexperts.com"""

        email = """Received: from spamexperts.com (spamexperts.com [5.79.73.204])
    by example.com
    (envelope-from <test@spamexperts.com>)"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_FROM'])

    def test_check_freemail_from_on_to_header(self):
        """sender@example.com on To header should not match example.com
        freemail domain"""
        lists = """freemail_domains example.com"""

        email = """To: sender@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    # Test check_freemail_replyto('replyto') and check_freemail_replyto('reply') eval rules

    def test_check_freemail_replyto_match_all_options(self):
        """example.com is freemail domain, Reply-To and From addresses are
        freemail domains but they are diferent so the check_freemail_replyto
        rules should match, also the check_freemail_from and
        check_freemail_header rules should match"""
        lists = """freemail_domains example.com"""

        email = """From: sender@example.com
Reply-To: test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 4, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_HEADER',
            'CHECK_FREEMAIL_REPLY', 'CHECK_FREEMAIL_REPLY_TO'])

    def test_check_freemail_replyto_dont_match_all_options(self):
        """Test case like above but no freemail domains defined"""
        email = """From: sender@example.com
Reply-To: test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_check_freemail_replyto_match_reply_option(self):
        """example.com is freemail domain From address is freemail domain and
        Reply-To header don't exist. Body contains a freemail domain email and the
        check_freemail_replyto('reply') rule should match, also check_freemail_from(),
        check_freemail_header(), and check_freemail_body() rules should match"""
        lists = """freemail_domains example.com"""

        email = """From: sender@example.com
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 4, ['CHECK_FREEMAIL_BODY', 'CHECK_FREEMAIL_FROM',
            'CHECK_FREEMAIL_HEADER', 'CHECK_FREEMAIL_REPLY'])

    def test_check_freemail_replyto_dont_match_reply_option(self):
        """Test case like above but no freemail domains defined"""
        email = """From: sender@example.com
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    # Tests for freemail_max_body_freemails config option

    def test_default_freemail_max_body_freemails(self):
        """If there are more than 3 freemails in body the FREEMAIL_BODY
        rule should not match"""
        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com test2@example.com test3@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_custom_freemail_max_body_freemails(self):
        """Same test case like above but with custom freemail_max_body_freemails"""
        opt = """freemail_max_body_freemails 1"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_zero_freemail_max_body_freemails(self):
        """Same test case like above but with freemail_max_body_freemails equal to zero"""
        opt = """freemail_max_body_freemails 0"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_negative_freemail_max_body_freemails(self):
        """Same test case like above but with freemail_max_body_freemails is negative"""
        opt = """freemail_max_body_freemails -1"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    # Tests for freemail_max_body_emails config option

    def test_default_freemail_max_body_emails(self):
        """If there are more than 3 emails in body (free or not free)
        the FREEMAIL_BODY rule should not match"""
        lists = """freemail_domains example.org"""

        email = """From: sender@example.net
        \nBody contains test@example.com test2@example.org test3@example.net
        test4@example.com test5@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_custom_freemail_max_body_emails(self):
        """Same test case like above but with custom freemail_max_body_emails"""
        opt = """freemail_max_body_emails 1"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_zero_freemail_max_body_emails(self):
        """Same test case like above but with freemail_max_body_emails equal to zero"""
        opt = """freemail_max_body_emails 0"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_negative_freemail_max_body_emails(self):
        """Same test case like above but with freemail_max_body_emails equal is negative"""
        opt = """freemail_max_body_emails -1"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 0, [])

    def test_freemail_max_body_emails_with_freemail_skip_when_over_max_option(self):
        """If there is more than one email in body (free or not free) the
        FREEMAIL_BODY rule should match if freemail_skip_when_over_max_option
        is disabled (set to zero)"""
        opt = """\nfreemail_max_body_emails 1
        \nfreemail_skip_when_over_max 0"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.net
        \nBody contains test@example.com"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 1, ['CHECK_FREEMAIL_BODY'])

    # Tests for freemail_skip_bulk_envfrom option

    def test_freemail_skip_bulk_envfrom_option_enabled(self):
        """CHECK_FREEMAIL_REPLY and CHECK_FREEMAIL_REPLY_TO should not match if
        a bulk email address (noreply@example.com) is present on Received header
        in envelope-from option"""
        lists = """freemail_domains example.com"""

        email = """From: sender@example.com
Reply-To: test@example.com
Received: from example.com (example.com [5.79.73.204])
    by example.com
    (envelope-from <noreply@example.com>)"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists)
        result = self.check_pad(email)
        self.check_report(result, 2, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_HEADER'])

    def test_freemail_skip_bulk_envfrom_option_disabled(self):
        """CHECK_FREEMAIL_REPLY and CHECK_FREEMAIL_REPLY_TO should match if
        a bulk email address (noreply@example.com) is present on Received header
        in envelope-from option and freemail_skip_bulk_envfrom option is disabled"""
        opt = """\nfreemail_skip_bulk_envfrom 0"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.com
Reply-To: test@example.com
Received: from example.com (example.com [5.79.73.204])
    by example.com
    (envelope-from <noreply@example.com>)"""

        self.setup_conf(config=CONFIG, pre_config=PRE_CONFIG + lists + opt)
        result = self.check_pad(email)
        self.check_report(result, 4, ['CHECK_FREEMAIL_FROM', 'CHECK_FREEMAIL_HEADER',
            'CHECK_FREEMAIL_REPLY', 'CHECK_FREEMAIL_REPLY_TO'])


    # Tests for freemail_add_describe_email option
    @unittest.skip("Test will fail because _REPORT_ don't have expected format")
    def test_freemail_add_describe_email_option_enabled(self):
        pre_config = """loadplugin Mail::SpamAssassin::Plugin::FreeMail
                        report _REPORT_
                    """

        lists = """freemail_domains example.com"""

        email = """From: sender@example.com"""

        expected_result = """*  1.0 CHECK_FREEMAIL_FROM Sender address is freemail
*      (sender[at]example.com)
*  1.0 CHECK_FREEMAIL_HEADER Header From is freemail
*      (sender[at]example.com)
"""

        self.setup_conf(config=CONFIG, pre_config=pre_config + lists)
        result = self.check_pad(email)
        self.assertEqual(result , expected_result)

    @unittest.skip("Test will fail because _REPORT_ don't have expected format")
    def test_freemail_add_describe_email_option_disabled(self):
        pre_config = """loadplugin Mail::SpamAssassin::Plugin::FreeMail
                        report _REPORT_
                    """

        opt = """freemail_add_describe_email 0"""

        lists = """freemail_domains example.com"""

        email = """From: sender@example.com"""

        expected_result = """*  1.0 CHECK_FREEMAIL_HEADER Header From is freemail
*  1.0 CHECK_FREEMAIL_FROM Sender address is freemail"""

        self.setup_conf(config=CONFIG, pre_config=pre_config + lists + opt)
        result = self.check_pad(email)
        self.assertEqual(result , expected_result)

    # TODO Tests for empty values config lines


def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestFunctionalFreeMail, "test"))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
