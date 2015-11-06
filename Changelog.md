# Changelog

## 0.9.1 / 2015-11-06

  - Improved add_units. Now it receives a hash. Refs #17. (Gabriel Parreiras)

## 0.9.0 / 2015-11-05

  - Add support for apps with more than one process type. Closes #17. See README instructions (Guilherme Garnier)

## 0.8.0 / 2015-10-28

  - Allow to invoke a WebHook after swap. Closes #16. See README instructions (Emerson Macedo)

## 0.7.0 / 2015-10-27

  - Allow to notify NewRelic deployment. Closes #12. See README instructions (Emerson Macedo)

## 0.6.1 / 2015-10-26

  - Abort task if before hook fails. Closes #13. (Guilherme Garnier)

## 0.6.0 / 2015-10-26

  - App that is not live stay with zero units. Closes #15, #8 (Guilherme Garnier and Emerson Macedo)

## 0.5.0 / 2015-10-26

  - Passing TAG environment variable to hooks. Closes #14. (Guilherme Garnier and Emerson Macedo)

## 0.4.1 / 2015-10-08

  - Enhancement: Add --force option to git push (Renan Carvalho)

## 0.4.0 / 2015-09-15

  - Feature: before and after hooks for each action (pre and swap). See README for instructions. (Guilherme Garnier)

## 0.3.2 / 2015-09-02

  - Support tsuru 0.12.0 API. It breaks add and remove units syntax. (Francisco Souza)

## 0.3.1 / 2015-01-07

  - Using response.read() to ensure the response stream is done until finish. (Emerson Macedo)

## 0.3.0 / 2014-10-07

  - Removed units option from configuration file. Use total units of live application. (Emerson Macedo)

## 0.2.1 / 2014-09-24

  - Plugin update to work with tsuru 0.7.0. Closes #3 (Emerson Macedo)

## 0.2.0 / 2014-09-22

  - Reduce and increase the number of units for blue and green instances, based on units configuration. Closes #1 (Emerson Macedo)

## 0.1.0 / 2014-08-26

  - Allow pre and swap actions (Emerson Macedo)
