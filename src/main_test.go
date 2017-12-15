package main

import (
	"testing"
)

func TestCname(t *testing.T) {
	expected := "login.tsuru.globotv.globoi.com"
	if cname := GetCname("login-blue"); cname != expected {
		t.Errorf("Expected cname value to be %s", expected)
	}
}
